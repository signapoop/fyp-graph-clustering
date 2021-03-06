import os
import argparse
import pathlib
import torch
import numpy as np

from learn_embedding import train
from core.EmbeddingDataSet import EmbeddingDataSet
from core.GraphConvNet import GraphConvNet
from core.SimpleNet import SimpleNet
from util.training_utils import get_oldest_net, save_metadata, save_train_log


def main(input_dir, output_dir, dataset_name, net_type, resume_folder, opt_parameters):
    # optimization parameters
    # opt_parameters = {}
    opt_parameters['learning_rate'] = 0.00075  # ADAM
    opt_parameters['max_iters'] = 360
    opt_parameters['batch_iters'] = 60
    opt_parameters['save_flag'] = True
    opt_parameters['decay_rate'] = 1.25
    opt_parameters['start_epoch'] = 0

    opt_parameters['distance_metric'] = 'cosine'
    # opt_parameters['graph_weight'] = 1.0  # Weight of graph cut loss
    opt_parameters['n_batches'] = 1
    opt_parameters['shuffle_flag'] = False
    opt_parameters['sampling_flag'] = False
    opt_parameters['val_batches'] = 1
    opt_parameters['perplexity'] = 30
    opt_parameters['early_exaggeration'] = 1.0
    opt_parameters['exploration_iters'] = 0

    opt_parameters['full_path_matrix'] = None
    data_root = os.path.join(input_dir, dataset_name)
    # opt_parameters['full_path_matrix'] = os.path.join(data_root, '{}_cutoff_max.npy'.format(dataset_name))
    # opt_parameters['full_path_matrix_cutoff'] = 1e6

    dataset = EmbeddingDataSet(dataset_name, input_dir, train=True)
    dataset.summarise()

    task_parameters = {}
    task_parameters['net_type'] = net_type
    task_parameters['n_components'] = 2
    task_parameters['val_flag'] = True

    net_parameters = {}
    net_parameters['n_components'] = task_parameters['n_components']
    net_parameters['D'] = dataset.input_dim  # input dimension
    net_parameters['H'] = 128  # number of hidden units
    net_parameters['L'] = 2  # number of hidden layers

    # Initialise network
    if net_type == 'graph':
        net = GraphConvNet(net_parameters)
    elif net_type == 'simple':
        net = SimpleNet(net_parameters)
        opt_parameters['max_iters'] = 1000
        opt_parameters['batch_iters'] = 50

    device = 'cpu'
    # if torch.cuda.is_available():
    #     net.cuda()
    #     device = 'cuda'

    if resume_folder != 'NA':
        checkpoint_dir = os.path.join(output_dir, resume_folder)
        net_filename, start_epoch = get_oldest_net(checkpoint_dir)
        checkpoint = torch.load(net_filename, map_location=device)
        print("Resuming training from: {}".format(net_filename))
        net.load_state_dict(checkpoint['state_dict'])
        opt_parameters['start_epoch'] = start_epoch
    else:
        # Create checkpoint dir
        subdirs = [x[0] for x in os.walk(output_dir) if dataset_name in x[0]]
        run_number = str(len(subdirs) + 1)
        checkpoint_dir = os.path.join(output_dir, dataset_name + '_' + run_number)
        pathlib.Path(checkpoint_dir).mkdir(exist_ok=True)  # create the directory if it doesn't exist

    print("Number of network parameters = {}".format(net.nb_param))
    print('Saving results into: {}'.format(checkpoint_dir))

    if 2 == 1:  # fast debugging
        opt_parameters['max_iters'] = 4
        opt_parameters['batch_iters'] = 1

    # Start training here
    val_dataset = None
    if task_parameters['val_flag']:
        val_dataset = EmbeddingDataSet(dataset_name, input_dir, train=False)

    tab_results = train(net, dataset, opt_parameters, checkpoint_dir, val_dataset, snapshot=True)

    end_epoch = opt_parameters['start_epoch'] + opt_parameters['max_iters']

    if opt_parameters['save_flag']:
        save_metadata(checkpoint_dir, task_parameters, net_parameters, opt_parameters, end_epoch)
        save_train_log(checkpoint_dir, tab_results, end_epoch)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Embedding net training')
    parser.add_argument('-i', '--input_dir', type=str, help='input dir')
    parser.add_argument('-o', '--output_dir', type=str, help='output dir')
    parser.add_argument('-d', '--dataset_name', type=str, help='name of dataset')
    parser.add_argument('-net', '--net_type', type=str, help='type of network')
    parser.add_argument('-r', '--resume_folder', type=str, default='NA', help='folder to resume from')
    args = parser.parse_args()

    print("Input directory: {}".format(args.input_dir))
    print("Output directory: {}".format(args.output_dir))
    print("Dataset name: {}".format(args.dataset_name))
    print("Network type: {}".format(args.net_type))
    print("Resume from folder: {}".format(args.resume_folder))

    # perplexity = [30]
    #graph_weight = np.linspace(0, 1, num=11)
    graph_weight = [0]
    for val in graph_weight:
        print("Graph weight = {}".format(val))
        opt_parameters = {'graph_weight': float(val)}

        main(args.input_dir, args.output_dir, args.dataset_name, args.net_type, args.resume_folder, opt_parameters)
