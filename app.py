from flask import Flask, request, jsonify
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import tempfile
import json
from flask import Flask
from flask_cors import CORS


# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

endpoint = os.getenv("AZURE_ENDPOINT", "https://skrdyide.cognitiveservices.azure.com/")
key = os.getenv("AZURE_KEY", "646ad626439a461882c80bda69c533ac")
model_id = os.getenv("AZURE_MODEL_ID", "Hospital_report")

document_analysis_client = DocumentAnalysisClient(
    endpoint=endpoint, credential=AzureKeyCredential(key)
)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Include all your analysis functions here (analyze_invoice, analyze_read, analyze_layout, analyze_receipt, analyze_document_general, analyze_document_prebuilt)
def analyze_invoice(file_path):
    with open(file_path, "rb") as f:
        poller = document_analysis_client.begin_analyze_document("prebuilt-invoice", document=f)
    result = poller.result()

    extracted_data = {}
    for invoice in result.documents:
        for field, value in invoice.fields.items():
            if value and value.value:
                if value.value_type == "currency":
                    extracted_data[field] = f"{value.value.amount} {value.value.symbol}"
                elif value.value_type == "string":
                    extracted_data[field] = value.value
                elif value.value_type == "dictionary":
                    for item_field, item_value in value.value.items():
                        if item_value and item_value.value:
                            if item_value.value_type == "currency":
                                extracted_data[item_field] = f"{item_value.value.amount} {item_value.value.symbol}"
                            elif item_value.value_type == "string":
                                extracted_data[item_field] = item_value.value
                            elif item_value.value_type == "float":
                                extracted_data[item_field] = item_value.value

    return extracted_data

def analyze_read(file_path):
    with open(file_path, "rb") as f:
        poller = document_analysis_client.begin_analyze_document("prebuilt-read", document=f)
    result = poller.result()

    extracted_data = {}
    key_elements = ["Date", "Time", "Discipline", "Notes"]
    current_key = None
    extracted_text = []
   
    for page in result.pages:
        for line in page.lines:
            cleaned_text = line.content.strip()
            if cleaned_text in key_elements:
                current_key = cleaned_text.lower()
                extracted_data[current_key] = []
            elif current_key and cleaned_text and cleaned_text != "=" and not cleaned_text.startswith("("):
                extracted_data[current_key].append(cleaned_text)
            elif cleaned_text and cleaned_text != "=" and not cleaned_text.startswith("("):
                extracted_text.append(cleaned_text)

    # Don't join the lines for key elements
    for key in extracted_data:
        if len(extracted_data[key]) == 1:
            extracted_data[key] = extracted_data[key][0]

    # Add other text directly to the extracted_data
    extracted_data["extracted_text"] = " ".join(extracted_text)
    
    return {'Details of the report': extracted_text}

def analyze_layout(file_path):
    with open(file_path, "rb") as f:
        poller = document_analysis_client.begin_analyze_document("prebuilt-layout", document=f)
    result = poller.result()

    extracted_data = []
    for page in result.pages:
        for line in page.lines:
            extracted_data.append(line.content)

        for selection_mark in page.selection_marks:
            extracted_data.append(f"Selection mark: {selection_mark.state}")

        for table in result.tables:
            extracted_data.append(f"Table has {table.row_count} rows and {table.column_count} columns")

    return {"text": "\n".join(extracted_data)}

def analyze_receipt(file_path):
    with open(file_path, "rb") as f:
        poller = document_analysis_client.begin_analyze_document("prebuilt-receipt", document=f)
    result = poller.result()

    extracted_data = {}
    for receipt in result.documents:
        receipt_type = receipt.doc_type
        if receipt_type:
            extracted_data["receipt_type"] = receipt_type

        merchant_name = receipt.fields.get("MerchantName")
        if merchant_name:
            extracted_data["merchant_name"] = merchant_name.value

        transaction_date = receipt.fields.get("TransactionDate")
        if transaction_date:
            extracted_data["transaction_date"] = transaction_date.value

        if receipt.fields.get("Items"):
            extracted_data["items"] = []
            for item in receipt.fields.get("Items").value:
                item_description = item.value.get("Description")
                if item_description:
                    extracted_data["items"].append({"description": item_description.value})

                item_quantity = item.value.get("Quantity")
                if item_quantity:
                    extracted_data["items"][-1]["quantity"] = item_quantity.value

                item_price = item.value.get("Price")
                if item_price:
                    extracted_data["items"][-1]["price"] = item_price.value

                item_total_price = item.value.get("TotalPrice")
                if item_total_price:
                    extracted_data["items"][-1]["total_price"] = item_total_price.value

        subtotal = receipt.fields.get("Subtotal")
        if subtotal:
            extracted_data["subtotal"] = subtotal.value

        tax = receipt.fields.get("TotalTax")
        if tax:
            extracted_data["tax"] = tax.value

        tip = receipt.fields.get("Tip")
        if tip:
            extracted_data["tip"] = tip.value

        total = receipt.fields.get("Total")
        if total:
            extracted_data["total"] = total.value

    return extracted_data

def analyze_document_general(file_path):
    with open(file_path, "rb") as f:
        poller = document_analysis_client.begin_analyze_document(model_id, document=f)
    result = poller.result()

    extracted_data = {}
    extracted_pages = set()

    for document in result.documents:
        for name, field in document.fields.items():
            field_value = field.value if field.value else field.content
            if field_value:
                extracted_data[name] = field_value
                if hasattr(field, 'bounding_regions'):
                    for region in field.bounding_regions:
                        extracted_pages.add(region.page_number)

    ocr_text = {}
    for page in result.pages:
        if page.page_number not in extracted_pages:
            page_text = []
            for line in page.lines:
                page_text.append(line.content)
            ocr_text[f'page_{page.page_number}'] = ' '.join(page_text)

    if ocr_text:
        extracted_data['additional_ocr_text'] = ocr_text

    return extracted_data

def analyze_document_prebuilt(file_path):
    with open(file_path, "rb") as f:
        poller = document_analysis_client.begin_analyze_document("prebuilt-document", document=f)
    result = poller.result()
    
    extracted_kv_pairs = {}
    remaining_text = []

    for document in result.documents:
        for name, field in document.fields.items():
            if field.value:
                extracted_kv_pairs[name] = field.value

    # Extract key-value pairs if available
    if hasattr(result, 'key_value_pairs'):
        for kv_pair in result.key_value_pairs:
            key = kv_pair.key.content if kv_pair.key else "N/A"
            value = kv_pair.value.content if kv_pair.value else "N/A"
            extracted_kv_pairs[key] = value

    # Extract remaining text
    for page in result.pages:
        for line in page.lines:
            if line.content not in extracted_kv_pairs.values():  # Exclude lines that are in key-value pairs
                remaining_text.append(line.content)

    return {
        'extracted_text': extracted_kv_pairs,
        'remaining_text': remaining_text  # Keep this as a list of lines
    }

def format_extracted_data(data):
    if isinstance(data, dict):
        result = []
        for k, v in data.items():
            if k == 'extracted_text':
                result.append("Extracted Text:")
                result.extend([f"  {sub_k}: {format_extracted_data(sub_v)}" for sub_k, sub_v in v.items()])
            elif k == 'remaining_text':
                result.append("\nRemaining Text:")
                result.extend([f"  {line}" for line in v])
            else:
                result.append(f"{k}: {format_extracted_data(v)}")
        return "\n".join(result)
    elif isinstance(data, list):
        return "\n".join([format_extracted_data(item) for item in data])
    else:
        return str(data)

@app.route('/')
def index():
    return jsonify({"message": "Welcome to the Document Analysis API"}), 200

@app.route('/api/analyze', methods=['POST'])
def analyze_document():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    analysis_type = request.form.get('analysis_type')
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        try:
            if analysis_type == "invoice":
                extracted_data = analyze_invoice(temp_file_path)
            elif analysis_type == "read":
                extracted_data = analyze_read(temp_file_path)
            elif analysis_type == "layout":
                extracted_data = analyze_layout(temp_file_path)
            elif analysis_type == "receipt":
                extracted_data = analyze_receipt(temp_file_path)
            elif analysis_type == "document":
                extracted_data = analyze_document_general(temp_file_path)
            elif analysis_type == "prebuilt-document":
                extracted_data = analyze_document_prebuilt(temp_file_path)
            else:
                return jsonify({"error": "Invalid analysis type"}), 400
            
            os.unlink(temp_file_path)  # Clean up the temporary file
            return jsonify(extracted_data)
        except Exception as e:
            os.unlink(temp_file_path)  # Ensure file is removed even if an error occurs
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Invalid file type"}), 400

if __name__ == '__main__':
    app.run(debug=True)