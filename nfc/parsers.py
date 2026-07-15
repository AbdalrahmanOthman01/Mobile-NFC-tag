import json
import base64
import logging

logger = logging.getLogger(__name__)

def make_vcard(first_name: str, last_name: str, phone: str, email: str, company: str, website: str) -> str:
    """Creates a standard vCard 3.0 formatted string."""
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"N:{last_name.strip()};{first_name.strip()};;;",
        f"FN:{first_name.strip()} {last_name.strip()}".strip(),
    ]
    if company.strip():
        lines.append(f"ORG:{company.strip()}")
    if phone.strip():
        lines.append(f"TEL;TYPE=CELL:{phone.strip()}")
    if email.strip():
        lines.append(f"EMAIL;TYPE=PREF,INTERNET:{email.strip()}")
    if website.strip():
        lines.append(f"URL:{website.strip()}")
    lines.append("END:VCARD")
    return "\n".join(lines)

def parse_vcard(vcard_text: str) -> dict:
    """Parses standard vCard 3.0 elements into a clean Python dictionary."""
    data = {
        "first_name": "",
        "last_name": "",
        "phone": "",
        "email": "",
        "company": "",
        "website": ""
    }
    lines = vcard_text.strip().split("\n")
    for line in lines:
        line = line.strip()
        if not line or ":" not in line:
            continue
        key_part, val = line.split(":", 1)
        key = key_part.split(";")[0].upper()
        val = val.strip()
        
        if key == "N":
            parts = val.split(";")
            if len(parts) > 0:
                data["last_name"] = parts[0].strip()
            if len(parts) > 1:
                data["first_name"] = parts[1].strip()
        elif key == "FN" and not (data["first_name"] or data["last_name"]):
            names = val.split(" ", 1)
            if len(names) == 1:
                data["first_name"] = names[0].strip()
            elif len(names) == 2:
                data["first_name"] = names[0].strip()
                data["last_name"] = names[1].strip()
        elif key == "TEL":
            data["phone"] = val
        elif key == "EMAIL":
            data["email"] = val
        elif key == "ORG":
            data["company"] = val
        elif key == "URL":
            data["website"] = val
            
    return data

def make_file_payload(filename: str, mime_type: str, file_content: str) -> str:
    """Serializes file information into a JSON string format."""
    encoded_content = base64.b64encode(file_content.encode("utf-8")).decode("utf-8")
    payload = {
        "name": filename.strip(),
        "mime": mime_type.strip(),
        "data": encoded_content
    }
    return json.dumps(payload)

def parse_file_payload(payload_text: str) -> dict:
    """Deserializes and decodes the file JSON payload structure."""
    try:
        data = json.loads(payload_text)
        decoded_bytes = base64.b64decode(data.get("data", ""))
        return {
            "name": data.get("name", "unnamed.bin"),
            "mime": data.get("mime", "application/octet-stream"),
            "content": decoded_bytes.decode("utf-8", errors="replace"),
            "raw_bytes": decoded_bytes
        }
    except Exception as e:
        logger.error(f"Error parsing file payload: {e}")
        return {
            "name": "error.bin",
            "mime": "application/octet-stream",
            "content": "",
            "raw_bytes": b""
        }
