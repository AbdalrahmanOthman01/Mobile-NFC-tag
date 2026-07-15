import logging
from typing import List, Dict, Any, Optional
from cryptography.fernet import Fernet
from database.connection import get_connection
from config import ENCRYPTION_KEY

logger = logging.getLogger(__name__)

# Initialize Fernet cipher with our secure key
cipher = Fernet(ENCRYPTION_KEY)

def encrypt_payload(payload: str) -> str:
    """Encrypts a string payload to a secure base64 string."""
    if not payload:
        return ""
    encrypted_bytes = cipher.encrypt(payload.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")

def decrypt_payload(encrypted_payload: str) -> str:
    """Decrypts a secure base64 string payload back to a plain string."""
    if not encrypted_payload:
        return ""
    decrypted_bytes = cipher.decrypt(encrypted_payload.encode("utf-8"))
    return decrypted_bytes.decode("utf-8")

def save_tag(uid: str, tag_type: str, name: str, payload: str, is_emulatable: bool = False) -> bool:
    """Saves or updates an NFC tag scan in the vault. Encrypts payload before writing."""
    encrypted = encrypt_payload(payload)
    is_emul_val = 1 if is_emulatable else 0
    
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO tags (uid, tag_type, name, payload_encrypted, is_emulatable)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(uid) DO UPDATE SET
                    tag_type = excluded.tag_type,
                    name = excluded.name,
                    payload_encrypted = excluded.payload_encrypted,
                    is_emulatable = excluded.is_emulatable;
                """,
                (uid, tag_type, name, encrypted, is_emul_val)
            )
        return True
    except Exception as e:
        logger.error(f"Error saving tag {uid}: {e}")
        return False
    finally:
        conn.close()

def get_tag_by_uid(uid: str) -> Optional[Dict[str, Any]]:
    """Retrieves an NFC tag by its UID and decrypts its payload."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, uid, tag_type, name, payload_encrypted, is_emulatable, created_at FROM tags WHERE uid = ?",
            (uid,)
        ).fetchone()
        
        if row:
            tag = dict(row)
            tag["payload"] = decrypt_payload(tag["payload_encrypted"])
            tag["is_emulatable"] = bool(tag["is_emulatable"])
            return tag
        return None
    except Exception as e:
        logger.error(f"Error reading tag {uid}: {e}")
        return None
    finally:
        conn.close()

def get_all_tags() -> List[Dict[str, Any]]:
    """Retrieves all saved tags from the vault, decrypting their payloads."""
    conn = get_connection()
    tags = []
    try:
        rows = conn.execute(
            "SELECT id, uid, tag_type, name, payload_encrypted, is_emulatable, created_at FROM tags ORDER BY created_at DESC"
        ).fetchall()
        
        for row in rows:
            tag = dict(row)
            try:
                tag["payload"] = decrypt_payload(tag["payload_encrypted"])
            except Exception as dec_err:
                logger.error(f"Failed to decrypt payload for tag {tag['uid']}: {dec_err}")
                tag["payload"] = "[Decryption Failed]"
            tag["is_emulatable"] = bool(tag["is_emulatable"])
            tags.append(tag)
    except Exception as e:
        logger.error(f"Error reading all tags: {e}")
    finally:
        conn.close()
    return tags

def delete_tag(uid: str) -> bool:
    """Removes a tag from the vault by UID."""
    conn = get_connection()
    try:
        with conn:
            conn.execute("DELETE FROM tags WHERE uid = ?", (uid,))
        return True
    except Exception as e:
        logger.error(f"Error deleting tag {uid}: {e}")
        return False
    finally:
        conn.close()

def log_written_record(payload_type: str, payload: str) -> bool:
    """Logs an NFC writing operation, encrypting the written data payload."""
    encrypted = encrypt_payload(payload)
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "INSERT INTO written_logs (payload_type, payload_encrypted) VALUES (?, ?)",
                (payload_type, encrypted)
            )
        return True
    except Exception as e:
        logger.error(f"Error logging written record: {e}")
        return False
    finally:
        conn.close()

def get_written_logs() -> List[Dict[str, Any]]:
    """Returns the history logs of written NFC tags."""
    conn = get_connection()
    logs = []
    try:
        rows = conn.execute(
            "SELECT id, payload_type, payload_encrypted, written_at FROM written_logs ORDER BY written_at DESC"
        ).fetchall()
        for row in rows:
            log_item = dict(row)
            try:
                log_item["payload"] = decrypt_payload(log_item["payload_encrypted"])
            except Exception:
                log_item["payload"] = "[Decryption Failed]"
            logs.append(log_item)
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
    finally:
        conn.close()
    return logs
