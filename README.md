Overviewer Merger
=================

Generate a single image for your Minecraft world, based on [Overviewer](https://overviewer.org/).

## Explanation

This program can be used to create a single image of your Minecraft world.
This program cannot generate maps on it's own.
It relies on the image files generated by [Overviewer](https://overviewer.org/).
A single image is easier to send to friends,
and it's also a lot smaller than the files generated by Overviewer.
This merger uses the convert command which is part of [ImageMagick](https://imagemagick.org).

## Configuration

There are a handful of configuration options.
The output of the --help argument is shown here:

```
usage: overviewer-merger [-h] [-t TEMP] [-e CONVERT_EXECUTABLE] [-m MEM]
                         [-d DEPTH] [-v] [-c] [-r RESIZE]
                         input output

Merge overviewer image tiles into a single image

positional arguments:
  input                 Input images generated by overviewer
  output                Output image file in png

optional arguments:
  -h, --help            show this help message and exit
  -t TEMP, --temp TEMP  Directory for temporary files
  -e CONVERT_EXECUTABLE, --convert-executable CONVERT_EXECUTABLE
                        Location for the ImageMagick convert executable
  -m MEM, --mem MEM     Memory limit GB for ImageMagick (default 8)
  -d DEPTH, --depth DEPTH
                        Limit the search depth to reduce the input image sizes
  -v, --verbose         If provided, ImageMagick commands will be called with
                        -monitor
  -c, --crop            If provided, crop the final image by removing
                        whitespace around
  -r RESIZE, --resize RESIZE
                        Resize the final image to a percentage of the total,
                        e.g. 50%
```
The input directory should point to ONE of the renders for your world,
not the overviewer output folder with the index.html and other files.
That means that you should pick any subfolder of the overviewer output folder as the input folder for this merger.
For example, if the name of your render is "normalrender", a very basic example could look like this:

`python3 overviewer-merger.py /path/to/overviewer/map/normalrender/ world.png`

### Temp

The example above can be expanded to more specific use cases by adding any of the mentioned options,
like changing the directory for the temporary files.
This option is highly recommended, as the default location is the OS specific temp directory,
which may not have enough space to combine the required images.

### Convert executable

By default, the "convert" command is used as the name (and location) for the ImageMagick convert command.
This can be changed, and is a required option to make this merger work on Windows.

### Depth

The depth option specifies the depth of which the overviewer images are used.
By default, the deepest level is used.
Overviewer generates images for each zoom level,
but for larger worlds the deepest level can prove too difficult to use.
As an example, for a fairly sized world I tested, there were 10 depth/zoom levels.
To combine the images for depth 6, it needed around 15GB disk space and a couple of minutes.
For a depth of 7, a lot more space was needed, around 50GB, and it took over half an hour.
The final image is only around 100MB, but ImageMagick needs a lot of disk space to process the images.
Of course this depends a lot on the world, overviewer render and merger configuration.

### Crop

By default, the image will be a perfect square,
with the world taking up just a portion of it.
With the crop option, the final image will be cropped to the actual world,
and remove any transparent empty space around it.

### Resize

There is also the option to resize the image to a percentage of the total size.
Adding this option with the value 100 will result in the option being ignored.

## License

This program was made by [Jelmer van Arnhem](https://github.com/Jelmerro).
It's licensed as free software under the terms of the MIT License, see LICENSE for details.
