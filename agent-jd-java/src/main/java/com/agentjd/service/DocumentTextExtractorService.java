package com.agentjd.service;

import java.nio.file.Path;

public interface DocumentTextExtractorService {
    String extract(Path path, String originalName, String contentType);
}
