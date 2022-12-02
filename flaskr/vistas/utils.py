from google.cloud import storage

#blob = a binary larg oBject is a collection of a binary data sotres as a single entity
def upload_to_bucket(blob_name,file_path,bucket_name):
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_file(file_path)
        return True
    except Exception as e:
        print(e)
        return False

def download_from_bucket(blob_name,file_path,bucket_name):
    print("download", file_path)
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        with open(file_path,'wb') as f:
                storage_client.download_blob_to_file(blob,f)        
        return True
    except Exception as e:
        print(e)
        return False

def delete_blob(blob_name,bucket_name):
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.delete()
        print(f"Blob {blob_name} deleted.")
        return True
    except Exception as e:
        print(e)
        return False

def check_blob_exists(blob_name,bucket_name):
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)        
        print(f"Blob {blob}")
        return True
    except Exception as e:
        print(e)
        return False