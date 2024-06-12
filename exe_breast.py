import argparse
import torch
import datetime
import json
import yaml
import datetime
import os

from src.main_model_table import TabCSDI
from src.utils_table import train, evaluate
from dataset_breast import get_dataloader

parser = argparse.ArgumentParser(description="TabCSDI")
parser.add_argument("--config", type=str, default="breast.yaml")
parser.add_argument("--device", default="cuda", help="Device")
parser.add_argument("--seed", type=int, default=1)
parser.add_argument("--testmissingratio", type=float, default=0.1)
parser.add_argument("--nfold", type=int, default=5, help="for 5-fold test")
parser.add_argument("--unconditional", action="store_true", default=0)
parser.add_argument("--modelfolder", type=str, default="")
parser.add_argument("--nsample", type=int, default=100)

args = parser.parse_args()
print(args)

os.environ["CUDA_LAUNCH_BLOCKING"] = "1"
start_time = datetime.datetime.now()
print("Start time:", start_time.strftime("%Y-%m-%d %H:%M:%S"))

path = "config/" + args.config
with open(path, "r") as f:
    config = yaml.safe_load(f)

config["model"]["is_unconditional"] = args.unconditional
config["model"]["test_missing_ratio"] = args.testmissingratio

print(json.dumps(config, indent=4))

# Create folder
current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
foldername = "./save/breast_fold" + str(args.nfold) + "_" + current_time + "/"
print("model folder:", foldername)
os.makedirs(foldername, exist_ok=True)
with open(foldername + "config.json", "w") as f:
    json.dump(config, f, indent=4)

# Every loader contains "observed_data", "observed_mask", "gt_mask", "timepoints"
train_loader, valid_loader, test_loader = get_dataloader(
    seed=args.seed,
    nfold=args.nfold,
    batch_size=config["train"]["batch_size"],
    missing_ratio=config["model"]["test_missing_ratio"],
)

model = TabCSDI(config, args.device).to(args.device)

if args.modelfolder == "":
    train(
        model,
        config["train"],
        train_loader,
        valid_loader=valid_loader,
        foldername=foldername,
    )
else:
    model.load_state_dict(torch.load("./save/" + args.modelfolder + "/model.pth"))
print("---------------Start testing---------------")
evaluate(model, test_loader, nsample=args.nsample, scaler=1, foldername=foldername)
complete_time = datetime.datetime.now()
print("Complete time:", complete_time.strftime("%Y-%m-%d %H:%M:%S"))

# Calculate and print the duration
duration = complete_time - start_time
print("Duration:", duration)
