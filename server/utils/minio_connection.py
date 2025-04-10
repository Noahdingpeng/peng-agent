from minio import Minio
from config.config import config
from utils.log import output_log
import os


class MinioStorage:
    def __init__(self):
        self.entrypoint = config.s3_url
        self.access_key = config.s3_access_key
        self.secret_key = config.s3_secret_key
        masked_secret_key = self.secret_key[:4] + "****" + self.secret_key[-4:]
        output_log(
            f"Minio connection to {self.entrypoint} with {self.access_key} and {masked_secret_key}",
            "debug",
        )
        self.client = Minio(
            self.entrypoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=True,
        )

    def file_upload(
        self, file_path, file_name, content_type, bucket_name=config.s3_bucket
    ):
        try:
            file_name = file_name.replace("\\", "/")
            self.client.fput_object(
                bucket_name, file_name, file_path, content_type=content_type
            )
            os.remove(file_path)
        except Exception as e:
            output_log(f"Error uploading file to Minio: {e}", "error")
            return False
        return True

    def file_download(self, file_name, download_path, bucket_name=config.s3_bucket):
        try:
            if len(file_name.split("://")) > 1:
                bucket_name = file_name.split("://")[0]
                file_name = file_name.split("://")[1]
            file_name = file_name.replace("\\", "/")
            file_name = file_name.replace("//", "/")
            self.client.fget_object(bucket_name, file_name, download_path)
        except Exception as e:
            output_log(f"Error downloading file from Minio: {e}", "error")
            return False
        return True

    def file_list_name(self, prefix="", bucket_name=config.s3_bucket):
        try:
            if len(prefix.split("://")) > 1:
                bucket_name = prefix.split("://")[0]
                prefix = prefix.split("://")[1]
            prefix = prefix.replace("\\", "/")
            prefix = prefix.replace("//", "/")
            output_log(
                f"Listing files from Minio with prefix {prefix}; Bucket_name: {bucket_name}",
                "debug",
            )
            objects = self.client.list_objects(
                bucket_name, prefix=prefix, recursive=True
            )
            return [obj.object_name for obj in objects]
        except Exception as e:
            output_log(f"Error listing files from Minio: {e}", "error")
            return None

    def file_exists(self, file_name, bucket_name=config.s3_bucket):
        try:
            file_name = file_name.replace("\\", "/")
            return self.client.stat_object(bucket_name, file_name)
        except Exception as e:
            output_log(f"Error checking file from Minio: {e}", "error")
            return False

    def remove_file(self, file_name, bucket_name=config.s3_bucket):
        try:
            self.client.remove_object(bucket_name, file_name)
        except Exception as e:
            output_log(f"Error removing file from Minio: {e}", "error")
            return False
        return True
