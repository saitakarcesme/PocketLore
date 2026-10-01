package org.pocketlore.app;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;

/** Durable intent marker; recovery restarts from the original provider, never resumes unknown bytes. */
final class ImportRecovery {
    static synchronized void begin(File directory, String kind) throws IOException {
        File stage = new File(directory, kind + "-import.pending.tmp");
        try (FileOutputStream out = new FileOutputStream(stage)) {
            out.write("Import interrupted. Select the original file to restart verification. Installed assets are retained.\n".getBytes(StandardCharsets.UTF_8));
            out.getFD().sync();
        }
        Files.move(stage.toPath(), new File(directory, kind + "-import.pending").toPath(),
            StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
    }
    static boolean pending(File directory, String kind) {
        return new File(directory, kind + "-import.pending").exists();
    }
    static void finish(File directory, String kind) throws IOException {
        Files.deleteIfExists(new File(directory, kind + "-import.pending").toPath());
    }
    private ImportRecovery() {}
}
