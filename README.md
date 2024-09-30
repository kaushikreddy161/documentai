# Document Intelligence Backend

This is a Flask-based API for document analysis using Azure AI Form Recognizer. It provides various endpoints for analyzing different types of documents, including invoices, receipts, and general documents.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## Installation

1. Clone the repository
2. Install the required dependencies:
3. Set up your Azure Form Recognizer service and obtain the endpoint and key
4. Create a `.env` file in the project root and add your Azure credentials:

## Usage
Run the Flask application:
# API Reference

## POST /api/analyze

Analyzes a document and returns extracted information based on the specified analysis type.

### Request

**URL**: `/api/analyze`

**Method**: `POST`

**Content-Type**: `multipart/form-data`

**Body Parameters**:
- `file`: The document file (required)
- `analysis_type`: Type of analysis to perform (required, string)

**Supported Analysis Types**:
- `invoice`
- `read`
- `layout`
- `receipt`
- `document`
- `prebuilt-document`

### Responses

#### Success Response

**Code**: `200 OK`

**Content**: JSON object containing the extracted information. The structure depends on the analysis type.

#### Error Responses

**Code**: `400 Bad Request`
- No file provided
- No selected file
- Invalid analysis type

**Code**: `500 Internal Server Error`
- Error during document analysis
The server will start on `http://localhost:5000`.

## API Reference

### POST /api/analyze

Analyzes a document and returns extracted information.

**Request Body:**
- `file`: The document file (multipart/form-data)
- `analysis_type`: Type of analysis to perform (invoice, read, layout, receipt, document, prebuilt-document)

**Response:**
JSON object containing the extracted information, structure depends on the analysis type.

For detailed API documentation, see [API_REFERENCE.md](docs/API_REFERENCE.md).

## Configuration

The application uses environment variables for configuration. See the [Installation](#installation) section for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.
