package com.agentjd.service.impl;

import com.agentjd.common.BizException;
import com.agentjd.common.ErrorCode;
import com.agentjd.service.DocumentTextExtractorService;
import org.apache.pdfbox.Loader;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;
import org.apache.poi.xwpf.usermodel.XWPFDocument;
import org.apache.poi.xwpf.usermodel.XWPFParagraph;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;
import java.util.stream.Collectors;

@Service
public class DocumentTextExtractorServiceImpl implements DocumentTextExtractorService {
    @Override
    public String extract(Path path, String originalName, String contentType) {
        try {
            String text;
            String name = originalName == null ? "" : originalName.toLowerCase(Locale.ROOT);
            String type = contentType == null ? "" : contentType.toLowerCase(Locale.ROOT);
            if (name.endsWith(".pdf") || type.contains("pdf")) {
                text = extractPdf(path);
            } else if (name.endsWith(".docx") || type.contains("wordprocessingml")) {
                text = extractDocx(path);
            } else {
                text = Files.readString(path, StandardCharsets.UTF_8);
            }
            String normalized = normalize(text);
            if (normalized.isBlank()) {
                throw new BizException(ErrorCode.PARAM_INVALID, "未解析到简历文本，请上传文本型 PDF、DOCX 或 TXT 文件");
            }
            return normalized;
        } catch (BizException ex) {
            throw ex;
        } catch (Exception ex) {
            throw new BizException(ErrorCode.PARAM_INVALID, "简历文件解析失败：" + ex.getMessage());
        }
    }

    private String extractPdf(Path path) throws IOException {
        try (PDDocument document = Loader.loadPDF(path.toFile())) {
            return new PDFTextStripper().getText(document);
        }
    }

    private String extractDocx(Path path) throws IOException {
        try (InputStream inputStream = Files.newInputStream(path);
                XWPFDocument document = new XWPFDocument(inputStream)) {
            return document.getParagraphs().stream()
                    .map(XWPFParagraph::getText)
                    .collect(Collectors.joining("\n"));
        }
    }

    private String normalize(String text) {
        return text == null ? "" : text.replace("\uFEFF", "").replace("ï»¿", "").replace("\u0000", "").trim();
    }
}
