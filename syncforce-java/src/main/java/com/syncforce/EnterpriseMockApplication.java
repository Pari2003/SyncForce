package com.syncforce;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import java.util.Map;

@SpringBootApplication
@RestController
public class EnterpriseMockApplication {

    public static void main(String[] args) {
        SpringApplication.run(EnterpriseMockApplication.class, args);
    }

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "ok", "service", "Java Enterprise Mock");
    }

    @PostMapping("/api/v1/sync")
    public Map<String, Object> receiveSyncData(@RequestBody Map<String, Object> payload) {
        System.out.println("Received sync payload: " + payload);
        // Simulate processing delay
        try { Thread.sleep(50); } catch (InterruptedException e) {}
        
        return Map.of(
            "status", "success",
            "receivedKeys", payload.keySet().size(),
            "message", "Data successfully synced with legacy enterprise system."
        );
    }
}
