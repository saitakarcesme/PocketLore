package org.pocketlore.app;

import java.io.*;
import java.security.MessageDigest;
import java.util.function.BooleanSupplier;

/** Bounded, cancellable staging. Caller validates GGUF with the runtime before atomic promotion. */
public final class ModelImport {
    public static final long MAX_BYTES = 512L * 1024 * 1024;
    public static final long RESERVE_BYTES = 32L * 1024 * 1024;
    public static String copy(InputStream input, File stage, long expected, long available,
                              BooleanSupplier cancelled) throws Exception {
        if (expected < 4 || expected > MAX_BYTES) throw new IOException("Model size must be known and at most 512 MiB");
        if (available < expected + RESERVE_BYTES) throw new IOException("Insufficient free storage for model copy and reserve");
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        long total = 0;
        byte[] buffer = new byte[65536];
        try (FileOutputStream output = new FileOutputStream(stage)) {
            int count;
            while ((count = input.read(buffer)) != -1) {
                if (cancelled.getAsBoolean()) throw new IOException("Cancelled");
                total += count;
                if (total > expected) throw new IOException("Model exceeds declared size");
                digest.update(buffer, 0, count); output.write(buffer, 0, count);
            }
            if (total != expected) throw new IOException("Incomplete model copy");
            output.getFD().sync();
        } catch (Exception error) { stage.delete(); throw error; }
        try (FileInputStream check = new FileInputStream(stage)) {
            if (check.read() != 'G' || check.read() != 'G' || check.read() != 'U' || check.read() != 'F') {
                stage.delete(); throw new IOException("Not a GGUF file");
            }
        }
        StringBuilder hash = new StringBuilder();
        for (byte b : digest.digest()) hash.append(String.format(java.util.Locale.ROOT, "%02x", b & 255));
        return hash.toString();
    }
    private ModelImport() {}
}
