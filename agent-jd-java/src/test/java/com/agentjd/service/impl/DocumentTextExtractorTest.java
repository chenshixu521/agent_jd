package com.agentjd.service.impl;

import com.agentjd.common.BizException;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class DocumentTextExtractorTest {
    private final DocumentTextExtractorServiceImpl extractor = new DocumentTextExtractorServiceImpl();

    @Test
    void extractsUtf8TextFile() throws Exception {
        Path file = Files.writeString(Files.createTempFile("resume", ".txt"), "Java Spring Boot Redis",
                StandardCharsets.UTF_8);

        String text = extractor.extract(file, "resume.txt", "text/plain");

        assertThat(text).contains("Java Spring Boot Redis");
    }

    @Test
    void removesUtf8BomFromTextFile() throws Exception {
        Path file = Files.createTempFile("resume-bom", ".txt");
        Files.write(file, new byte[] { (byte) 0xEF, (byte) 0xBB, (byte) 0xBF, 'J', 'a', 'v', 'a' });

        String text = extractor.extract(file, "resume.txt", "text/plain");

        assertThat(text).isEqualTo("Java");
    }

    @Test
    void rejectsEmptyExtractedText(@TempDir Path tempDir) throws Exception {
        Path file = Files.writeString(tempDir.resolve("empty.txt"), "   ", StandardCharsets.UTF_8);

        assertThatThrownBy(() -> extractor.extract(file, "empty.txt", "text/plain"))
                .isInstanceOf(BizException.class)
                .hasMessageContaining("未解析到简历文本");
    }
}
