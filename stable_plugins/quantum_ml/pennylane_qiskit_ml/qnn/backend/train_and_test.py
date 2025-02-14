# Copyright 2023 QHAna plugin runner contributors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# implementation based on:
# https://github.com/XanaduAI/quantum-transfer-learning/blob/master/dressed_circuit.ipynb
# https://pennylane.ai/qml/demos/tutorial_quantum_transfer_learning.html

# PyTorch
import torch

import time
from torch.nn import Module
from torch.utils.data.dataloader import DataLoader
from torch.nn.modules.loss import _Loss
from torch.optim.optimizer import Optimizer


def train(
    model: Module,
    dataloader: DataLoader,
    loss_fn: _Loss,
    optimizer: Optimizer,
    num_iterations: int,
    weights_to_wiggle: int,
):
    """
    train the model with the given data and parameters

    model: network to train
    X_train: training input data
    Y_train: trianing labels
    loss_fn: loss function
    optimizer: optimizer
    num_iterations: amount of batches to use during training
    n_classes: number of classes used for classication
    batch_size: number of training elements per batch
    """

    # TRAINING
    model.train()
    torch.set_grad_enabled(True)

    for i in range(num_iterations):
        start_it_time = time.time()

        correctly_labeled = 0
        for train_data, train_labels in dataloader:
            if weights_to_wiggle != 0:
                rnd_indices = torch.randperm(len(model.q_params))[weights_to_wiggle:]
                for idx in rnd_indices:
                    model.q_params[idx].requires_grad = False

            # zero gradients
            optimizer.zero_grad(set_to_none=True)

            # get model predictions
            predictions = model(train_data)

            # calculate loss
            loss = loss_fn(predictions, train_labels)

            # backpropagation, adjust weights
            loss.backward()

            optimizer.step()

            # accuracy
            predicted_class = torch.argmax(predictions, dim=1)
            labels = torch.argmax(train_labels, dim=1)
            correctly_labeled += float(torch.sum(predicted_class == labels).item())

            # time
            total_it_time = time.time() - start_it_time
            minutes_it = total_it_time // 60
            seconds_it = round(total_it_time - minutes_it * 60)

            if weights_to_wiggle != 0:
                for idx in rnd_indices:
                    model.q_params[idx].requires_grad = True

        # print loss, accuracy and time of this iteration
        accuracy = correctly_labeled / len(dataloader.dataset)
        print(
            "Iter: {}/{} Time: {:.4f} min {:.4f} sec with loss: {:.4f} and accuracy: {:.4f} on the training data".format(
                i + 1, num_iterations, minutes_it, seconds_it, loss.item(), accuracy
            )
        )
    model.eval()
    torch.set_grad_enabled(False)


def test(
    model: Module, X_test: torch.Tensor, Y_test: torch.Tensor, loss_fn: _Loss
) -> float:
    """
    test the model with the given data and parameters

    model: network to test
    X_test: test data
    Y_test: test labels
    loss_fn: loss function
    n_classes: number of classes used in the classification
    """
    # TEST
    model.eval()
    torch.set_grad_enabled(False)

    # feed test data into network and get predictions
    predictions = model(X_test)

    # compute loss
    test_loss = loss_fn(predictions, Y_test)

    # accuracy
    predicted_class = torch.argmax(predictions, dim=1)
    Y_test = torch.argmax(Y_test, dim=1)
    test_accuracy = float(torch.sum(predicted_class == Y_test).item()) / len(Y_test)

    # print loss and accuracy for test data
    print(
        "Test loss: {:.4f} and accuracy: {:.4f} on the test data".format(
            test_loss.item(), test_accuracy
        )
    )
    return test_accuracy
