import logging
import os
import shutil
import zipfile
import datetime
import argparse
import json


version = "1.1"


def log_config():
    """performs a logging basic setup"""
    handler_to_file = logging.FileHandler("log.log", "w")
    handler_to_file.setLevel(logging.DEBUG)
    handler_to_console = logging.StreamHandler()
    handler_to_console.setLevel(logging.ERROR)
    logging.basicConfig(
        handlers=[
            handler_to_file,
            handler_to_console,
        ],
        format="%(asctime)s: %(levelname)s %(filename)s %(lineno)s: %(message)s",
        level=logging.DEBUG,
    )


def clinterface():
    logging.debug("importing arguments provided by user")
    parser = argparse.ArgumentParser(
        prog="Copia Backups",
        description="Runs backup routines saved in a separate JSON file",
    )
    parser.version = version
    parser.add_argument(
        "r",
        action="store",
        nargs="+",
        help="backup routine name",
    )
    parser.add_argument(
        "-v",
        "--verify",
        action="store_true",
        help="verification after backup",
    )
    parser.add_argument(
        "-c",
        "--compress",
        action="store_true",
        help="backup will be compressed",
    )
    parser.add_argument(
        "-t",
        "--timestamp",
        action="store_false",
        help="no timestamp prefixes",
    )
    args = parser.parse_args()

    return vars(args)


class JsonImporter:
    def __init__(self):
        self.routines = None
        # the json file should be in the same folder
        folder_path = os.path.dirname(os.path.realpath(__file__))
        basename = "routines.json"
        self.json_file_path = os.path.join(folder_path, basename)

    def import_routines(self):
        self.routines = json.load(open(self.json_file_path, "r"))


class RoutineMgr:
    def __init__(self, args, routines):
        self.args = args
        self.routines = routines

    def run(self):
        for routine in self.args["r"]:
            logging.debug("starting routine %s", routine)
            copy_mgr = CopyMgr()
            for src in self.routines[routine]["sources"]:
                copy_mgr.add_src(src)
            for dst in self.routines[routine]["destinations"]:
                copy_mgr.add_dst(dst)
            copy_mgr.check_paths()

            if self.args["compress"] == False:
                copy_mgr.copy_all(
                    verify=self.args["verify"], timestamp=self.args["timestamp"]
                )
            elif self.args["compress"] == True:
                copy_mgr.zip_all(
                    verify=self.args["verify"], timestamp=self.args["timestamp"]
                )


class CopyMgr:
    """manages the process of copying/compressing files from multiple source paths to multiple destination paths"""

    # performs checks of the paths provided
    # it allows verifying each file and folder after the copying process finishes (optional)

    def __init__(self):
        self.source_paths = []
        self.destination_paths = []
        self.paths_ok = False
        logging.debug("copy manager created")

    def add_src(self, path):
        self.source_paths.append(path)
        logging.debug("source path added: %s", path)

    def remove_list_element(list_object, pos):
        """remove from list preventing IndexError"""
        if pos < len(list_object):
            list_object.pop(pos)
            logging.debug("element in position %s removed from %s", pos, list_object)
        else:
            logging.error("can't remove position %s in %s ", pos, list_object)

    # this method will be used when creating the gui
    def rem_src(self, position):
        logging.debug("removing source path in position %s", position)
        self.remove_list_element(self.source_paths, position)

    def add_dst(self, path):
        self.destination_paths.append(path)
        logging.debug("destination path added: %s", path)

    # this method will be used when creating the gui
    def rem_dst(self, position):
        logging.debug("removing destination path in position %s", position)
        self.remove_list_element(self.destination_paths, position)

    def check_paths(self):
        """checks provided paths"""
        # it checks both self.source_paths and self.destination_paths (lists)
        # the result of the operation is saved in self.paths_ok as boolean

        logging.debug("checking paths provided")

        def check_paths_in_list(paths_list, path_type=""):
            """checking paths provided in a list"""
            for path in paths_list:
                exists = os.path.exists(path)
                if not exists:
                    # here the possibility of adding code to create the non existent folder in case the path_type="destination" remains open - future problem
                    self.paths_ok = False
                    raise Exception(
                        "following {} path doesn't exist: {}".format(path_type, path)
                    )
                elif exists:
                    if path_type == "destination" and not os.path.isdir(path):
                        self.paths_ok = False
                        raise Exception(
                            "following destination path is supposed to be a directory and it is not: {}".format(
                                path
                            )
                        )
                    else:
                        logging.debug("this %s path exists: %s", path_type, path)

        try:
            # initially set to True - set to False if errors found
            self.paths_ok = True
            # paths are checked
            check_paths_in_list(self.source_paths, path_type="source")
            check_paths_in_list(self.destination_paths, path_type="destination")
        except Exception:
            logging.exception(
                "error while checking the paths provided; while this error present files will not be allowed to be copied"
            )

    def copy_all_verify(self, timestamp=""):
        """verifies if each file got copied"""
        # It walks through all the source roots and checks if every dir and file exists in the destination folders in the expected location
        # It only checks the existence of the dirs and files in the destination folders.
        logging.debug("verify method started")
        err_count = 0
        for path_s in self.source_paths:
            logging.debug(
                "verifying source path %s: %s",
                self.source_paths.index(path_s) + 1,
                path_s,
            )
            logging.debug(
                "source path %s will be checked for all destination folders (total amount = %s)",
                self.source_paths.index(path_s) + 1,
                len(self.destination_paths),
            )
            if os.path.isdir(path_s):
                src_root_no = 0
                for root, dirs, files in os.walk(path_s):
                    src_root_no += 1
                    logging.debug("    source root %s: %s", src_root_no, root)
                    for path_d in self.destination_paths:
                        # verifying destination root equivalent
                        if root != path_s:
                            my_basename = timestamp + str(os.path.basename(path_s))
                            string_length = len(root) - len(path_s) - 1
                            root_d = os.path.join(
                                path_d, my_basename, root[-string_length:]
                            )
                        else:
                            my_basename = timestamp + str(os.path.basename(path_s))
                            root_d = os.path.join(path_d, my_basename)
                        logging.debug(
                            "    destination root %s: %s", src_root_no, root_d
                        )
                        if not os.path.exists(root_d):
                            logging.error(
                                "    this directory was not created: %s", root_d
                            )
                            err_count += 1
                        else:
                            # during the iterations each dir ends up being considered also as a root. Because of that we don't check dirs - with only roots suffices
                            for file in files:
                                logging.debug(
                                    "    source file %s", os.path.join(root, file)
                                )
                                logging.debug(
                                    "    destination file %s",
                                    os.path.join(root_d, file),
                                )
                                if not os.path.exists(os.path.join(root_d, file)):
                                    logging.error(
                                        "    this file was not created: %s", dir
                                    )
                                    err_count += 1
                logging.debug(
                    "finished verifying source path %s: %s",
                    self.source_paths.index(path_s) + 1,
                    path_s,
                )
            elif os.path.isfile(path_s):
                for path_d in self.destination_paths:
                    my_basename = timestamp + str(os.path.basename(path_s))
                    dst = os.path.join(path_d, my_basename)
                    if not os.path.exists(dst):
                        logging.error("        this file was not created: %s", dst)
                        err_count += 1

        if err_count > 0:
            logging.debug(
                "verify method finished; amount of errors found: %s", err_count
            )
        else:
            logging.debug("verify method finished - no errors found")

    def zip(self, src, dst, timestamp=""):
        """compresses one source file/folder(main) into one destination folder"""
        path_z = os.path.join(dst, timestamp + os.path.basename(src) + ".zip")
        zf = zipfile.ZipFile(path_z, "w", zipfile.ZIP_DEFLATED)
        abs_src = os.path.abspath(src)
        if os.path.isdir(src):
            for dirname, subdirs, files in os.walk(src):
                # the files lead the compressing process - if there is an empty folder in src it will not be taken on count
                for filename in files:
                    absname = os.path.abspath(os.path.join(dirname, filename))
                    logging.debug("        absname is %s", absname)
                    arcname = absname[len(abs_src) + 1 :]
                    logging.debug("        arcname is %s", arcname)
                    logging.debug(
                        "        zipping %s as %s",
                        os.path.join(dirname, filename),
                        arcname,
                    )
                    zf.write(absname, arcname)
        elif os.path.isfile(src):
            absname = src
            logging.debug("absname is %s", src)
            arcname = os.path.basename(src)
            logging.debug("arcname is %s", arcname)
            zf.write(absname, arcname)
        zf.close()

    def zip_all_verify(self, timestamp=""):
        """verifies if each file got zipped"""
        # It walks through all the source roots and checks if for each one of the there is a .zip file in the expected location
        # It only checks the existence of the .zip files in the destination folders.
        logging.debug("verify method for .zip backup started")
        err_count = 0
        for path_s in self.source_paths:
            logging.debug(
                "verifying source path %s: %s",
                self.source_paths.index(path_s) + 1,
                path_s,
            )
            logging.debug(
                "source path %s will be checked for all destination folders (total amount = %s)",
                self.source_paths.index(path_s) + 1,
                len(self.destination_paths),
            )
            for path_d in self.destination_paths:
                my_basename = timestamp + str(os.path.basename(path_s))
                dst = os.path.join(path_d, my_basename + ".zip")
                if not os.path.exists(dst):
                    logging.error("this zipped file was not created: %s", dst)
                    err_count += 1
        logging.debug(
            "verify method for .zip backup finished; amount of errors found: %s",
            err_count,
        )

    def zip_all(self, verify=False, timestamp=True):
        """compresses all the source files/folders into all the destination folders"""
        logging.debug(
            "request received: to compress all source files and folders into all the destination folders"
        )
        try:
            # checking paths
            if not self.paths_ok:
                raise Exception(
                    "files can't be compressed because paths have not been checked"
                )

            # timestamp
            my_timestamp = ""
            if timestamp:
                my_timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M_")

            # zip process
            for path_d in self.destination_paths:
                logging.debug("compressing into destination: %s", path_d)
                for path_s in self.source_paths:
                    logging.debug("    compressing from origin: %s", path_s)
                    self.zip(path_s, path_d, timestamp=my_timestamp)
            if verify:
                self.zip_all_verify(timestamp=my_timestamp)
            logging.debug("compressing process finished")
        except Exception:
            logging.exception("error while compressing")

    def copy_all(self, verify=False, timestamp=False):
        """copies all source files and folders into all the destination folders"""
        # the function can only run if self.paths_ok = True
        # if verify=True the additional task of verifying every file in every destination will be performed
        logging.debug(
            "request received: to copy all source files and folders into all the destination folders"
        )
        try:
            # checking paths
            if not self.paths_ok:
                raise Exception(
                    "files can't be copied because paths have not been checked"
                )

            # timestamp
            my_timestamp = ""
            if timestamp == True:
                my_timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M_")

            # copying
            for path_d in self.destination_paths:
                logging.debug("copying into destination: %s", path_d)
                for path_s in self.source_paths:
                    logging.debug("    copying from origin: %s", path_s)
                    if os.path.isdir(path_s):
                        my_basename = my_timestamp + str(os.path.basename(path_s))
                        dst = os.path.join(path_d, my_basename)
                        shutil.copytree(path_s, dst)
                    elif os.path.isfile(path_s):
                        my_basename = my_timestamp + str(os.path.basename(path_s))
                        dst = os.path.join(path_d, my_basename)
                        shutil.copy2(path_s, dst)
                    else:
                        logging.error(
                            "neither a folder or file - not copied: %s", path_s
                        )
            # verifying
            if verify == True:
                self.copy_all_verify(timestamp=my_timestamp)
            logging.debug("copying process finished")
        except Exception:
            logging.exception("error while copying")


if __name__ == "__main__":
    import logging
    import os

    # configuring log
    log_config()
    logging.debug("Copia Backups v%s started - script by lmponcio", version)

    # importing arguments
    arguments = clinterface()

    # importing routines
    json_import = JsonImporter()
    json_import.import_routines()

    # running
    my_routines = RoutineMgr(arguments, json_import.routines)
    my_routines.run()
