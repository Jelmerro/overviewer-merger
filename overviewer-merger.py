import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile

# overviewer-merger was created by Jelmer van Arnhem,
# and can be copied under the terms of the MIT.
# See the LICENSE and README.md for details, or find the project on github:
# https://github.com/Jelmerro/overviewer-merger


class Merger:

    def __init__(self, cli_args):
        # input dir
        self.input_dir = cli_args.input
        if not self.input_dir.endswith(os.path.sep):
            self.input_dir += os.path.sep
        # temp location
        self.temp = os.path.join(cli_args.temp, "overviewer-merger-temp")
        self.env = os.environ.copy()
        self.env["MAGICK_TEMPORARY_PATH"] = self.temp
        self.env["MAGICK_TMPDIR"] = self.temp
        # convert executable location
        self.convert = cli_args.convert_executable
        # memory limit
        self.memory_limit = ""
        if cli_args.mem:
            self.memory_limit = "-limit memory {}GB ".format(cli_args.mem)
        # depth
        self.depth = cli_args.depth
        # verbose output
        self.monitor_text = ""
        if cli_args.verbose:
            self.monitor_text = "-monitor "
        # crop
        self.crop = cli_args.crop
        # resize
        self.resize = cli_args.resize
        # output file
        self.output_file = cli_args.output
        if not self.output_file.endswith(".png"):
            self.output_file += ".png"

    def process(self):
        self.cleanup()
        # Generate rows
        rows = self.generate_rows()
        # Merge rows
        final_image = os.path.join(self.temp, "out.png")
        self.run_convert_command(
            "-append {} {}".format(" ".join(rows), final_image),
            "Merging rows into single image (this is the longest step)")
        # post processing
        if self.crop:
            new_image = os.path.join(self.temp, "out-cropped.png")
            self.run_convert_command(
                "{} -fuzz 80% -trim +repage {}".format(final_image, new_image),
                "Cropping image")
            final_image = new_image
        percent = self.resize
        if percent != 100:
            new_image = os.path.join(self.temp, "out-resized.png")
            self.run_convert_command(
                "{} -resize {}% {}".format(final_image, percent, new_image),
                "Resizing image to {}% of the original size".format(percent))
            final_image = new_image
        shutil.move(final_image, self.output_file)
        # cleanup
        self.cleanup()
        print("All done :)")

    def run_command(self, command):
        return subprocess.run(
            command.split(),
            check=True,
            stdout=subprocess.PIPE,
            env=self.env).stdout

    def run_convert_command(self, command_args, title):
        print(title)
        command = "{} {}{}{}".format(
            self.convert, self.monitor_text, self.memory_limit, command_args)
        try:
            self.run_command(command)
        except subprocess.CalledProcessError as e:
            print(e)
            print("{} process failed, see error log above".format(
                title.split()[0]))
            self.cleanup()
            sys.exit(1)

    def cleanup(self):
        print("Cleaning temporary files")
        shutil.rmtree(self.temp, ignore_errors=True)

    def generate_rows(self):
        print("Scanning for the image files")
        files = self.get_file_list()
        if not files:
            if self.depth:
                print("Directory contains no overviewer images for this depth")
            else:
                print("Directory does not contain any overviewer images")
            sys.exit(1)
        first_file = files[0]
        self.generate_empty_file_from_example(first_file)
        width = self.calculate_width(first_file)
        print("Starting merge process for {} rows".format(width))
        rows = []
        for row_number in range(0, width):
            print("Generating row {}".format(row_number))
            row_file = os.path.join(self.temp, "row-{}.png".format(row_number))
            rows.append(row_file)
            row_files = []
            for number in range(0, width):
                row_files.append(self.file_path_from_number(
                    files, self.calculate_width(first_file, False),
                    number, row_number))
            command = "{} {}+append {} {}".format(
                self.convert, self.memory_limit, " ".join(row_files), row_file)
            self.run_command(command)
        print("Done generating rows")
        return rows

    def get_file_list(self):
        location = os.path.join(
            self.input_dir, "**{}*.png".format(os.path.sep))
        all_files = []
        for f in glob.glob(location, recursive=True):
            directory = os.path.dirname(os.path.realpath(f))
            files_in_dir = os.listdir(directory)
            if self.depth:
                if self.calculate_width(f, False) == self.depth:
                    all_files.append(f)
            else:
                max_depth = True
                for file_in_dir in files_in_dir:
                    if os.path.isdir(os.path.join(directory, file_in_dir)):
                        max_depth = False
                        break
                if max_depth:
                    all_files.append(f)
        return all_files

    def calculate_width(self, f, powered=True):
        if powered:
            return 2 ** len(
                f.replace(self.input_dir, "", 1).split(os.path.sep))
        else:
            return len(f.replace(self.input_dir, "", 1).split(os.path.sep))

    def file_path_from_number(self, files, bits, number, row):
        number = "{{:0{}b}}".format(bits).format(number)
        row = "{{:0{}b}}".format(bits).format(row)
        file_number = ""
        for i in range(0, len(number)):
            if row[i] == "1":
                file_number += str(int(number[i]) + 2)
            else:
                file_number += number[i]
        path = ""
        for char in file_number:
            path += char + os.path.sep
        path = path[:-1]
        path += ".png"
        path = os.path.join(self.input_dir, path)
        if path in files:
            return path
        return os.path.join(self.temp, "empty.png")

    def generate_empty_file_from_example(self, f):
        os.makedirs(self.temp, exist_ok=True)
        command = '{} {} -format %wx%h info:'.format(self.convert, f)
        size = self.run_command(command).decode().strip()
        command = '{} -size {} xc:none {}'.format(
            self.convert, size, os.path.join(self.temp, "empty.png"))
        self.run_command(command)


if __name__ == "__main__":
    # Parsing arguments for files, folders and settings
    parser = argparse.ArgumentParser(
        prog="overviewer-merger",
        description="Merge overviewer image tiles into a single image")
    parser.add_argument("input", help="Input images generated by overviewer")
    parser.add_argument(
        "-t", "--temp", help="Directory for temporary files",
        default=tempfile.gettempdir(), type=str)
    parser.add_argument(
        "-e", "--convert-executable",
        help="Location for the ImageMagick convert executable",
        default="convert", type=str)
    parser.add_argument(
        "-m", "--mem",
        help="Memory limit GB for ImageMagick (default 8)",
        default=8, type=int)
    parser.add_argument(
        "-d", "--depth",
        help="Limit the search depth to reduce the input image sizes",
        default=0, type=int)
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="If provided, ImageMagick commands will be called with -monitor")
    parser.add_argument(
        "-c", "--crop", action="store_true",
        help="If provided, crop the final image by removing whitespace around")
    parser.add_argument(
        "-r", "--resize",
        help="Resize the final image to a percentage of the total, e.g. 50%%",
        default=100, type=int)
    parser.add_argument("output", help="Output image file in png")
    # Create Merger object and start processsing
    Merger(parser.parse_args()).process()
