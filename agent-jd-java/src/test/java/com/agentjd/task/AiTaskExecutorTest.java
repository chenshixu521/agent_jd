package com.agentjd.task;

import com.agentjd.agent.AgentClient;
import com.agentjd.entity.AiTask;
import com.agentjd.entity.AiTaskStatus;
import com.agentjd.mapper.AiTaskMapper;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class AiTaskExecutorTest {

    @Test
    void executesPendingTaskAndStoresSuccess() {
        AiTaskMapper mapper = mock(AiTaskMapper.class);
        AgentClient agentClient = mock(AgentClient.class);
        AiTaskSupport support = mock(AiTaskSupport.class);
        AiTask task = task(AiTaskStatus.PENDING);
        when(mapper.selectOne(any())).thenReturn(task);
        when(support.input(task)).thenReturn(Map.of("jd_text", "Java Redis"));
        when(agentClient.call("jd", "analyze", "task-1", Map.of("jd_text", "Java Redis")))
                .thenReturn(Map.of("keywords", java.util.List.of("Java", "Redis")));
        when(support.toJson(any())).thenReturn("{\"keywords\":[\"Java\",\"Redis\"]}");

        AiTaskExecutor.ExecutionResult result = new AiTaskExecutor(mapper, agentClient, support).execute("task-1");

        assertEquals(AiTaskExecutor.ExecutionResult.SUCCESS, result);
        assertEquals(AiTaskStatus.SUCCESS.getCode(), task.getStatus());
        assertEquals(100, task.getProgress());
        verify(mapper, org.mockito.Mockito.times(2)).updateById(task);
        verify(support, org.mockito.Mockito.times(2)).cache(task);
    }

    @Test
    void skipsTaskThatIsAlreadyFinished() {
        AiTaskMapper mapper = mock(AiTaskMapper.class);
        AgentClient agentClient = mock(AgentClient.class);
        AiTaskSupport support = mock(AiTaskSupport.class);
        when(mapper.selectOne(any())).thenReturn(task(AiTaskStatus.SUCCESS));

        AiTaskExecutor.ExecutionResult result = new AiTaskExecutor(mapper, agentClient, support).execute("task-1");

        assertEquals(AiTaskExecutor.ExecutionResult.ALREADY_FINISHED, result);
        verify(agentClient, never()).call(any(), any(), any(), any());
    }

    private AiTask task(AiTaskStatus status) {
        AiTask task = new AiTask();
        task.setTaskUuid("task-1");
        task.setUserId(1L);
        task.setCapability("jd");
        task.setAction("analyze");
        task.setInputJson("{\"jd_text\":\"Java Redis\"}");
        task.setTraceId("trace-1");
        task.setStatus(status.getCode());
        task.setProgress(0);
        return task;
    }
}
