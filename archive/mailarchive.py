import hashlib
from mailbox import Maildir
from pathlib import Path
from tempfile import TemporaryDirectory, TemporaryFile
import yaml
from archive import Archive
from archive.tools import tmp_chdir


class MailArchive(Archive):

    def create(self, path, mails, compression='xz', comment=None):
        path = Path(path)
        with TemporaryDirectory(prefix="mailarchive-") as tmpdir:
            with tmp_chdir(tmpdir):
                basedir = Path(path.name.split('.')[0])
                maildir = Maildir(str(basedir), create=True)
                self.mailindex = []
                last_folder = None
                for folder, msgbytes in mails:
                    if folder != last_folder:
                        mailfolder = maildir.add_folder(folder)
                        last_folder = folder
                    sha256 = hashlib.sha256(msgbytes).hexdigest()
                    key = mailfolder.add(msgbytes)
                    msg = mailfolder.get_message(key)
                    idx_item = {
                        "Date": msg.get("Date"),
                        "From": msg.get("From"),
                        "MessageId": msg.get("Message-Id"),
                        "Subject": msg.get("Subject"),
                        "To": msg.get("To"),
                        "checksum": { "sha256": sha256 },
                        "folder": folder,
                        "key": key,
                    }
                    self.mailindex.append(idx_item)
                with TemporaryFile(dir=tmpdir) as tmpf:
                    head = "%YAML 1.1\n"
                    if comment:
                        head += "# %s\n" % comment
                    tmpf.write(head.encode("ascii"))
                    yaml.dump(self.mailindex, stream=tmpf, encoding="ascii",
                              default_flow_style=False, explicit_start=True)
                    tmpf.seek(0)
                    self.add_metadata(".mailindex.yaml", tmpf)
                    super().create(path, compression, [basedir])
        return self
