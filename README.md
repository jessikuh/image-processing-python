# Solus Orbis Avatar Processing (Deprecated)

This is an application utilizing FastAPI to resize and compress avatars. It is deprecated due to being milliseconds to a second slower than its Node counterpart.

## Experimentation

The use of the AWS CLI was tested to see if uploading to S3 would be faster. However, in production, using this method added a second to the upload time, making it even slower.
