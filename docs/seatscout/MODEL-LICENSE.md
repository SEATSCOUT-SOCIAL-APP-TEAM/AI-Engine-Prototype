# The model in this folder

`model/yolo11n.onnx` is Ultralytics YOLO11n, trained on COCO, exported to ONNX at 512 × 512:

```bash
pip install ultralytics
yolo export model=yolo11n.pt format=onnx imgsz=512 opset=17 simplify=True
```

YOLO11 is released by Ultralytics under the [AGPL-3.0 licence](https://github.com/ultralytics/ultralytics/blob/main/LICENSE). This folder (the SeatScout browser demo) is published under the same licence, with its full source in this repository.

The sample clips are not stored here. They stream from [Mixkit](https://mixkit.co/) under the Mixkit free licence.
