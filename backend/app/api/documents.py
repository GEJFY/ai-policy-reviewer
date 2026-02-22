"""
API endpoints for Document management.

このモジュールはPDF文書のアップロード、OCR処理、テキスト抽出機能を提供する。
アップロードされた文書は非同期でOCR処理され、レビュー可能な状態に変換される。

主要機能:
    - PDFファイルのアップロード
    - マルチプロバイダーOCR処理（Azure Doc Intel / Tesseract / AWS Tesseract）
    - テキストのチャンク分割とベクトル埋め込み生成
    - 文書の一覧・詳細取得
    - 抽出テキストの参照

文書のライフサイクル:
    1. POST /documents/upload でPDFアップロード（ocr_status: pending）
    2. バックグラウンドでOCR処理開始（ocr_status: processing）
    3. テキスト抽出→チャンク分割→埋め込み生成
    4. 処理完了（ocr_status: completed）
    5. レビュー作成が可能に

依存サービス:
    - OCRServiceFactory: マルチプロバイダーOCR
    - ChunkingService: テキスト分割
    - EmbeddingService: ベクトル埋め込み生成
"""

import os
import uuid
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    BackgroundTasks,
    Query,
)
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.models.document import Document, DocumentChunk
from app.models.review import Review, ReviewFinding, ReviewCheckItem
from app.models.comparison import (
    ComparisonProject,
    ComparisonCheckItem,
    ComparisonResult,
)
from app.models.document_group import DocumentGroupMember
from app.schemas.document import (
    DocumentResponse,
    DocumentChunkResponse,
    DocumentUploadResponse,
)
from app.services.ocr_service import ocr_service
from app.services.chunking_service import chunking_service
from app.services.embedding_service import embedding_service
from app.core.logging_config import get_logger
from app.core.exceptions import FileTooLargeError
from app.config import settings

# モジュール専用ロガー
logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])

# Upload directory / ファイルサイズ上限（設定から取得）
UPLOAD_DIR = settings.upload_dir
MAX_FILE_SIZE = settings.max_file_size_mb * 1024 * 1024


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    ocr_status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Get list of documents with optional filtering."""
    query = db.query(Document)

    if ocr_status:
        query = query.filter(Document.ocr_status == ocr_status)

    return query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get a specific document by ID."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    """
    PDFファイルをアップロードし、OCR処理を開始する。

    アップロードされたファイルは固有のUUIDファイル名で保存され、
    バックグラウンドでOCR処理が開始される。即座にレスポンスを返す。

    処理フロー:
        1. ファイル形式の検証（.pdfのみ許可）
        2. アップロードディレクトリの作成（存在しない場合）
        3. UUID生成によるユニークなファイル名でファイル保存
        4. Documentレコードの作成（ocr_status: pending）
        5. OCRバックグラウンドタスクのスケジュール
        6. レスポンス返却

    Args:
        file: アップロードするPDFファイル（multipart/form-data）
        background_tasks: バックグラウンドタスクハンドラ
        db: データベースセッション

    Returns:
        DocumentUploadResponse: アップロード結果
            - id: 文書ID
            - title: 元のファイル名
            - file_path: サーバー上の保存パス
            - ocr_status: "pending"
            - message: 状態メッセージ

    Raises:
        HTTPException(400): PDF以外のファイルがアップロードされた場合

    Note:
        OCR完了確認はGET /documents/{id}でocr_statusを確認。
        Azure Document Intelligenceが利用不可の場合はPyPDF2で代替処理。
    """
    # Validate file type
    filename = file.filename or "unknown.pdf"
    allowed_extensions = (".pdf", ".xlsx", ".xls")
    if not filename.lower().endswith(allowed_extensions):
        raise HTTPException(
            status_code=400,
            detail="Supported file types: PDF, Excel (.xlsx, .xls)",
        )

    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Generate unique filename
    file_ext = os.path.splitext(filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Save file
    content = await file.read()

    # ファイルサイズ上限チェック
    if len(content) > MAX_FILE_SIZE:
        raise FileTooLargeError(file_size=len(content), max_size=MAX_FILE_SIZE)

    with open(file_path, "wb") as f:
        f.write(content)

    # Determine file type
    ext = os.path.splitext(filename)[1].lower()
    file_type = "excel" if ext in (".xlsx", ".xls") else "pdf"

    # Create document record
    document = Document(
        title=filename,
        file_path=file_path,
        file_type=file_type,
        ocr_status="pending",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Schedule OCR processing
    if background_tasks:
        background_tasks.add_task(process_document_ocr, document.id)

    return DocumentUploadResponse(
        id=document.id,
        title=document.title,
        file_path=document.file_path,
        ocr_status=document.ocr_status,
        message="Document uploaded. OCR processing will start shortly.",
    )


@router.post("/{document_id}/ocr", response_model=DocumentResponse)
async def trigger_ocr(
    document_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Manually trigger OCR processing for a document."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Reset status
    document.ocr_status = "pending"
    db.commit()

    # Schedule OCR
    background_tasks.add_task(process_document_ocr, document_id)

    return document


@router.delete("/{document_id}", status_code=204)
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Delete a document and its associated data."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete file
    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    # Delete related records that reference this document
    # (SQLite does not support ON DELETE CASCADE via ALTER TABLE)

    # 1. Reviews and their findings/check_items (cascade from Review)
    reviews = db.query(Review).filter(Review.document_id == document_id).all()
    for review in reviews:
        db.query(ReviewFinding).filter(ReviewFinding.review_id == review.id).delete()
        db.query(ReviewCheckItem).filter(
            ReviewCheckItem.review_id == review.id
        ).delete()
    db.query(Review).filter(Review.document_id == document_id).delete()

    # 2. Comparison projects referencing this document
    # Delete results and check_items for each project first
    projects = (
        db.query(ComparisonProject)
        .filter(
            (ComparisonProject.parent_document_id == document_id)
            | (ComparisonProject.subsidiary_document_id == document_id)
        )
        .all()
    )
    for project in projects:
        db.query(ComparisonResult).filter(
            ComparisonResult.project_id == project.id
        ).delete()
        db.query(ComparisonCheckItem).filter(
            ComparisonCheckItem.project_id == project.id
        ).delete()
    db.query(ComparisonProject).filter(
        (ComparisonProject.parent_document_id == document_id)
        | (ComparisonProject.subsidiary_document_id == document_id)
    ).delete(synchronize_session="fetch")

    # 3. Document group memberships
    db.query(DocumentGroupMember).filter(
        DocumentGroupMember.document_id == document_id
    ).delete()

    db.delete(document)
    db.commit()
    return None


@router.get("/{document_id}/chunks", response_model=list[DocumentChunkResponse])
async def get_document_chunks(document_id: int, db: Session = Depends(get_db)):
    """Get document chunks."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
        .all()
    )
    return chunks


@router.get("/{document_id}/text")
async def get_document_text(document_id: int, db: Session = Depends(get_db)):
    """Get extracted text from a document."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.ocr_status != "completed":
        raise HTTPException(status_code=400, detail="OCR not completed")

    return {"text": document.extracted_text}


def _update_ocr_progress(document_id: int, progress: str):
    """OCR進捗を短いトランザクションで更新する。"""
    from app.db.database import SessionLocal

    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.ocr_progress = progress
            db.commit()
    except Exception:
        pass
    finally:
        db.close()


async def process_document_ocr(document_id: int):
    """
    バックグラウンドでPDFのOCR処理を実行する。

    DB書き込みロックの長時間保持を避けるため、処理を3フェーズに分割:
        Phase 1: ステータス更新（短いDB書き込み）
        Phase 2: テキスト抽出・チャンク分割・埋め込み生成（DBロックなし）
        Phase 3: 結果をDBに一括保存（短いDB書き込み）

    Args:
        document_id: 処理対象の文書ID
    """
    from app.db.database import SessionLocal

    logger.info(f"Starting OCR processing: document_id={document_id}")

    # === Phase 1: ステータスをprocessingに更新（短いトランザクション） ===
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.warning(f"Document not found for OCR: document_id={document_id}")
            return
        file_path = document.file_path
        document.ocr_status = "processing"
        document.ocr_progress = "テキスト抽出中..."
        db.commit()
    finally:
        db.close()

    # === Phase 2: テキスト抽出・チャンク・埋め込み生成（DBロックなし） ===
    try:
        # Determine file type from extension
        is_excel = file_path.lower().endswith((".xlsx", ".xls"))

        # Extract text
        extracted_text = ""
        if is_excel:
            try:
                from app.services.excel_parser import extract_text_from_excel

                extracted_text = extract_text_from_excel(file_path)
                logger.info(
                    f"Excel text extracted: document_id={document_id}, "
                    f"chars={len(extracted_text)}"
                )
            except Exception as e:
                logger.error(
                    f"Excel extraction failed: document_id={document_id}, error={e}"
                )
        else:
            # PDF: まずPyPDF2でテキスト抽出を試みる
            try:
                import PyPDF2

                with open(file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    pages = [page.extract_text() or "" for page in reader.pages]
                    extracted_text = "\n\n".join(pages).strip()
            except Exception as e:
                logger.warning(
                    f"PyPDF2 text extraction failed: document_id={document_id}, error={e}"
                )

        if len(extracted_text) > 100:
            logger.info(
                f"Text extracted successfully: document_id={document_id}, "
                f"chars={len(extracted_text)}"
            )
        elif not is_excel and ocr_service.is_available():
            logger.info(
                f"Using {ocr_service.provider_name()} for OCR: "
                f"document_id={document_id}"
            )
            _update_ocr_progress(document_id, "OCRテキスト抽出中...")
            extracted_text = await ocr_service.extract_text_from_pdf(file_path)
        else:
            logger.warning(
                f"No OCR available and PyPDF2 extraction insufficient: "
                f"document_id={document_id}"
            )

        logger.info(
            f"Text extracted: document_id={document_id}, length={len(extracted_text)}"
        )

        # Hierarchical chunking (section-aware)
        _update_ocr_progress(document_id, "チャンク分割中...")
        chunk_results = chunking_service.chunk_text_hierarchical(extracted_text)
        logger.info(
            f"Text chunked: document_id={document_id}, "
            f"chunks={len(chunk_results)}, "
            f"sections={len(set(c.section_title for c in chunk_results if c.section_title))}"
        )

        # Generate embeddings (slow API calls - NO DB lock held)
        total_chunks = len(chunk_results)
        chunk_data = []
        for i, chunk_result in enumerate(chunk_results):
            if embedding_service.is_available() and total_chunks > 0:
                _update_ocr_progress(
                    document_id,
                    f"埋め込み生成中 ({i + 1}/{total_chunks})...",
                )
            embedding_bytes = None
            if embedding_service.is_available():
                try:
                    embedding = await embedding_service.get_embedding(
                        chunk_result.content
                    )
                    embedding_bytes = embedding_service.embedding_to_bytes(embedding)
                except Exception as e:
                    logger.warning(
                        f"Failed to generate chunk embedding: chunk={i}, error={e}"
                    )
            chunk_data.append(
                {
                    "chunk_index": i,
                    "section_title": chunk_result.section_title,
                    "content": chunk_result.content,
                    "embedding": embedding_bytes,
                }
            )

        # === Phase 3: 結果をDBに一括保存（短いトランザクション） ===
        _update_ocr_progress(document_id, "データベース保存中...")
        db = SessionLocal()
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                logger.warning(
                    f"Document disappeared during OCR: document_id={document_id}"
                )
                return

            document.extracted_text = extracted_text

            # Delete existing chunks
            db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).delete()

            # Insert all chunks
            for cd in chunk_data:
                chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=cd["chunk_index"],
                    section_title=cd["section_title"],
                    content=cd["content"],
                    embedding=cd["embedding"],
                )
                db.add(chunk)

            document.ocr_status = "completed"
            document.ocr_progress = ""
            db.commit()
            logger.info(f"OCR processing completed: document_id={document_id}")
        finally:
            db.close()

    except Exception as e:
        logger.error(
            f"OCR processing failed: document_id={document_id}, error={e}",
            exc_info=True,
        )
        db = SessionLocal()
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.ocr_status = "failed"
                document.ocr_progress = "エラーが発生しました"
                db.commit()
        except Exception as rollback_err:
            logger.error(
                f"Failed to update status to failed: document_id={document_id}, "
                f"error={rollback_err}"
            )
        finally:
            db.close()
