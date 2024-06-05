import paramiko
import os

class GoogleSFTPConnection:
    def __init__(self, host, username, private_key_path):
        self.host = host
        self.username = username
        self.private_key_path = private_key_path
        self.client = None

    def connect(self):
        try:
            private_key = paramiko.RSAKey.from_private_key_file(self.private_key_path)
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(self.host, username=self.username, pkey=private_key)
            print("Connected to Google server successfully!")
            return True
        except paramiko.AuthenticationException as e:
            print("Authentication failed:", str(e))
            return False
        except paramiko.SSHException as e:
            print("SSH connection failed:", str(e))
            return False
        except paramiko.Exception as e:
            print("Error:", str(e))
            return False

    def disconnect(self):
        if self.client is not None:
            self.client.close()
            print("Disconnected from Google server.")

    def upload_file(self, local_path, remote_path, file_name):
        try:
            sftp = self.client.open_sftp()

            try:
                sftp.stat(remote_path)
                print(f"Exists remote directory: {remote_path}")
            except FileNotFoundError:
                sftp.mkdir(remote_path)
                print(f"Created remote directory: {remote_path}")

            local_path = os.path.abspath(local_path).replace("\\", "/")
            
            sftp.put(local_path, f"{remote_path}/{file_name}")
            print(f"Uploaded file '{local_path}' to '{remote_path}' successfully!")
        except Exception as ex:
            print("Error during file upload:", str(ex))