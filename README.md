# RealTime Motion Detection

You can download the video clip which is used in the demo at: https://box.bw-sw.com/f/c629c692d5c04b7caac6/?dl

Work example at: https://youtu.be/FCme11alEmc

## Detector usage

See `example.py` for usage.

## Detector parameters

* `bg_subs_scale_percent` - how much to scale initial frame before movement detection occurs (default 1/4);
* `bg_history` - the length of background accumulator ring buffer (default 15);
* `bg_history_collection_period_max` - defines how often update background ring buffer with frames from movement (default 1 - every frame);
* `movement_frames_history` - how much frames to keep in movement accumulator ring buffer (default 5);
* `brightness_discard_level` - threshold which is used to detect movement from the noise (default 20);
* `pixel_compression_ratio` - how much to compress the initial video for boxes search (default 20), means that every 20x20 px of initial frame will be resized to 1x1 of detection frame;
* `group_boxes` - group overlapping boxes into a single one or just keep them as they are (default True);
* `expansion_step` - how big is expansion algoritm step when it searches for boxes, lower steps lead to smaller performance and close objects are detected as separate, bigger step leads to faster algorithm performance and close objects can be detected as a single one.

 
