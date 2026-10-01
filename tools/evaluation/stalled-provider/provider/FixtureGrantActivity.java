package org.pocketlore.app;

/** Issues scoped fixture URI grants after instrumentation starts the target process. */
public final class FixtureGrantActivity extends android.app.Activity {
    @Override public void onCreate(android.os.Bundle state){
        super.onCreate(state);
        for(String kind:new String[]{"model","pack"})for(String mode:new String[]{"stall-empty","stall-prefix","short","retry"})
            grantUriPermission("org.pocketlore.app",android.provider.DocumentsContract.buildDocumentUri("org.pocketlore.fixture.documents",kind+"-"+mode),android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION);
        finish();
    }
}
