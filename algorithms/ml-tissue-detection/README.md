# Machine Learning Tissue Detection
Train semantic segmentation machine learning (SSML) models to detect tissue in low resolution (e.g. thumbnail) whole-slide-images (WSIs). 

SSMLs models are implemented using PyTorch's DeepLabV3 implementation. The training and evaluation dataset include 539 WSIs (from Emory University and UC Davis) used during the YOLO Braak stage project. The tissue labels were created using HistomicsTK tissue detection function and further refined for correctness using a custom-build Jupyter interactive with HistomicsUI annotation integration.