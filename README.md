# 🚀 Simple PDF-to-Text Converter

Uses latest, cutting-edge technology for accuracy.

Convert any PDF to high-quality Text in seconds using Mistral's state-of-the-art OCR technology. This lightweight app provides the most advanced and affordable OCR solution on the market, powered by [Mistral OCR](https://mistral.ai/news/mistral-ocr).

![Mistral OCR Benchmarks](https://mistral.ai/images/ocr/ocr-benchmark-chart.png)

## ✨ Features

- **Superior Accuracy**: Leverages Mistral OCR's 94.89% accuracy rate, outperforming Google, Azure, and OpenAI models
- **Complex Document Handling**: Perfectly handles tables, math equations, multi-column layouts, and more
- **Multilingual Support**: Process documents in any language with exceptional accuracy
- **Easy-to-Use Interface**: Both GUI and CLI options available
- **Clipboard Integration**: Copy markdown with one click
- **Secure API Key Management**: Save your API key securely through the UI

## 🔧 Quick Start

1. **Get a Mistral API key**
   - Create a free experimental API key at [Mistral AI Platform](https://console.mistral.ai/)

2. **Install dependencies**:
   ```bash
   pip install requests tk
   ```

3. **Run the application**:
   ```bash
   python simple_pdf_to_md.py
   ```

4. **Enter your API key**:
   - When the app launches, you'll see an API key field at the top
   - Enter your Mistral API key
   - Click "Save API Key" to securely store it
   - The key will be remembered for future sessions

For CLI users:
   ```bash
   python pdf_to_md_cli.py input.pdf [output.md]
   ```

## 📊 Why Mistral OCR?

According to [Mistral's benchmarks](https://mistral.ai/news/mistral-ocr), their OCR technology significantly outperforms competitors:

| Model                | Overall | Math  | Multilingual | Scanned | Tables |
|----------------------|---------|-------|--------------|---------|--------|
| Google Document AI   | 83.42   | 80.29 | 86.42        | 92.77   | 78.16  |
| Azure OCR            | 89.52   | 85.72 | 87.52        | 94.65   | 89.52  |
| GPT-4o-2024-11-20    | 89.77   | 87.55 | 86.00        | 94.58   | 91.70  |
| **Mistral OCR**      | **94.89** | **94.29** | **89.55** | **98.96** | **96.12** |

## 📷 How It Works

The application:
1. Uploads your PDF to Mistral's secure API
2. Processes the document using advanced OCR technology
3. Returns perfectly formatted Markdown
4. Makes copying or saving the result easy

## 📝 Use Cases

- Convert academic papers to markdown format
- Transform scanned documents into editable text
- Prepare documents for RAG systems
- Extract content from complex tables and diagrams
- Digitize multilingual documents

## 🔒 Security

- Your API key is stored securely in `~/.mistral_pdf/config.json`
- Keys are masked in the UI for privacy
- No data is stored permanently
- Processing happens via Mistral's secure API

## 📚 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Built with ❤️ for the document processing community. For any questions, please open an issue on GitHub. 