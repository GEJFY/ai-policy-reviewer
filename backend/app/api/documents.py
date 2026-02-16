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
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Save file
    content = await file.read()

    # ファイルサイズ上限チェック
    if len(content) > MAX_FILE_SIZE:
        raise FileTooLargeError(file_size=len(content), max_size=MAX_FILE_SIZE)

    with open(file_path, "wb") as f:
        f.write(content)

    # Create document record
    document = Document(
        title=file.filename,
        file_path=file_path,
        file_type="pdf",
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


async def process_document_ocr(document_id: int):
    """
    バックグラウンドでPDFのOCR処理を実行する。

    Azure Document Intelligenceを使用してテキストを抽出し、
    チャンク分割とベクトル埋め込み生成を行う。
    Azureサービスが利用不可の場合はPyPDF2にフォールバック。

    処理フロー:
        1. 文書ステータスをprocessingに更新
        2. OCRサービスでテキスト抽出（Azure DIまたはPyPDF2）
        3. テキストをチャンクに分割（ChunkingService）
        4. 既存チャンクを削除（再処理対応）
        5. 各チャンクにベクトル埋め込みを生成
        6. チャンクをDBに保存
        7. ステータスをcompletedに更新

    Args:
        document_id: 処理対象の文書ID

    エラーハンドリング:
        - OCR失敗時: ocr_status=failedに更新
        - 埋め込み生成失敗: 警告ログを出力し、埋め込みなしで続行
        - 例外発生時: ステータスをfailedに更新し、ログ記録

    生成データ:
        - Document.extracted_text: 抽出されたフルテキスト
        - DocumentChunk: チャンク分割されたテキストと埋め込みベクトル

    Note:
        大規模PDFの場合、処理に数分かかる場合がある。
        スキャンPDFはAzure Document Intelligenceで高精度OCR。
        テキストPDFはPyPDF2でも処理可能。
    """
    from app.db.database import SessionLocal

    logger.info(f"Starting OCR processing: document_id={document_id}")

    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.warning(f"Document not found for OCR: document_id={document_id}")
            return

        # Update status
        document.ocr_status = "processing"
        db.commit()

        try:
            # Extract text - まずPyPDF2でテキスト抽出を試みる
            extracted_text = ""
            try:
                import PyPDF2

                with open(document.file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    pages = [page.extract_text() or "" for page in reader.pages]
                    extracted_text = "\n\n".join(pages).strip()
            except Exception as e:
                logger.warning(
                    f"PyPDF2 text extraction failed: document_id={document_id}, error={e}"
                )

            if len(extracted_text) > 100:
                # テキストベースPDF: PyPDF2で十分なテキストが取れた
                logger.info(
                    f"Using PyPDF2 for text PDF: document_id={document_id}, "
                    f"chars={len(extracted_text)}"
                )
            elif ocr_service.is_available():
                # スキャンPDF: OCRが必要
                logger.info(
                    f"Using {ocr_service.provider_name()} for OCR: document_id={document_id}"
                )
                extracted_text = await ocr_service.extract_text_from_pdf(
                    document.file_path
                )
            else:
                logger.warning(
                    f"No OCR available and PyPDF2 extraction insufficient: "
                    f"document_id={document_id}"
                )

            document.extracted_text = extracted_text
            logger.info(
                f"Text extracted: document_id={document_id}, length={len(extracted_text)}"
            )

            # Chunk the text
            chunks = chunking_service.chunk_text(extracted_text)
            logger.info(
                f"Text chunked: document_id={document_id}, chunks={len(chunks)}"
            )

            # Delete existing chunks
            db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).delete()

            # Create new chunks with embeddings
            for i, chunk_text in enumerate(chunks):
                embedding_bytes = None
                if embedding_service.is_available():
                    try:
                        embedding = await embedding_service.get_embedding(chunk_text)
                        embedding_bytes = embedding_service.embedding_to_bytes(
                            embedding
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to generate chunk embedding: chunk={i}, error={e}"
                        )

                chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=i,
                    content=chunk_text,
                    embedding=embedding_bytes,
                )
                db.add(chunk)

            document.ocr_status = "completed"
            db.commit()
            logger.info(f"OCR processing completed: document_id={document_id}")

        except Exception as e:
            logger.error(
                f"OCR processing failed: document_id={document_id}, error={e}",
                exc_info=True,
            )
            document.ocr_status = "failed"
            db.commit()

    finally:
        db.close()
