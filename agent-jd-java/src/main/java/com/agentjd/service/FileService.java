package com.agentjd.service;

import com.agentjd.entity.FileObject;
import com.agentjd.vo.FileVO;
import org.springframework.core.io.Resource;
import org.springframework.web.multipart.MultipartFile;

public interface FileService {
    FileVO upload(MultipartFile file);

    FileVO detail(Long id);

    Resource download(Long id);

    FileObject requireOwnFile(Long id);
}
