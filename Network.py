import numpy as np
from tqdm import tqdm
from utils import ReLU, d_ReLU, L2Loss, d_L2Loss


class Network(object):

    def __init__(self, layer_dimensions):
        """
        initialize the networks parameters using kaiming initialization (we used ReLU activation)

        :param layer_dimensions: dimensions of linear layers
        """

        self.layer_dimensions = layer_dimensions
        self.weights = [np.random.normal(0.0, np.math.sqrt(2 / in_dim), size=(out_dim, in_dim)) for in_dim, out_dim in
                        zip(self.layer_dimensions[:-1], self.layer_dimensions[1:])]
        self.biases = [np.zeros((dim, 1)) for dim in self.layer_dimensions[1:]]

    def SGD(self, epochs, lr, batch_size, train, test=None):
        """

        :param epochs: number of iterations over the dataset
        :param lr: learning rate
        :param batch_size:
        :param train: train set
        :param test: test set
        :return: lists of weight sizes, test and train losses over epochs
        """
        num_of_batches = len(train) // batch_size
        training_losses = []
        test_losses = []
        avg_weights = []
        for epoch in tqdm(range(epochs)):
            np.random.shuffle(train)
            batches = np.array_split(train, num_of_batches)
            training_loss = 0
            for batch in batches:
                training_loss += self.batch_step(batch, lr)
            training_losses.append(training_loss / len(train))
            avg_weights.append(self.average_weights())
            if test is not None:
                test_loss = self.evaluate_test(test)
                test_losses.append(test_loss)
        return {"train_loss": training_losses, "test_loss": test_losses, "avg_weight": avg_weights}

    def batch_step(self, batch, lr):
        """
         preform on step of gradient descent w.r.t batch
        :param batch: batch of samples
        :param lr: learning rate
        :return: loss over the batch
        """
        batch_eval = 0
        partial_ws = [np.zeros(w.shape) for w in self.weights]
        partial_bs = [np.zeros(b.shape) for b in self.biases]
        for x, y in batch:
            partial_ws_x, partial_bs_x, loss_x = self.backward(x, y)  # calculate gradient w.r.t parameters at point x,y
            partial_ws = [w + w_x for w, w_x in zip(partial_ws, partial_ws_x)]
            partial_bs = [b + b_x for b, b_x in zip(partial_bs, partial_bs_x)]
            batch_eval += loss_x
        self.weights = [w - (lr / len(batch)) * d_w for w, d_w in
                        zip(self.weights, partial_ws)]  # make gradient descent step
        self.biases = [b - (lr / len(batch)) * d_b for b, d_b in zip(self.biases, partial_bs)]

        return batch_eval

    def forward(self, x):
        """
        evaluate the network N on input x
        :param x: input value
        :return: N(x)
        """
        a = x.reshape(-1, 1)
        for w, b in zip(self.weights[:-1], self.biases[:-1]):
            a = ReLU(np.dot(w, a) + b)
        return np.dot(self.weights[-1], a) + self.biases[-1]

    def backward(self, x, y):
        """
        calculate gradient
        use the following terminology:
            c (/c_l) - the output of a (l indexed) linear layer pre activation
            a - activation(c) i.e activation applied to c
            delta (/delta_l) - the current partial derivative of the loss w.r.t the parameters of the l'th layer
        :param x: input sample
        :param y: output sample
        :return: gradient evaluated at parameters
        """
        # Apply network on input x and store all intermediate values (before and after activations)
        a = x.reshape(-1, 1)
        c_values = []  # pre-activation
        a_values = [a]  # post-activation

        for w, b in zip(self.weights[:-1], self.biases[:-1]):
            c = np.dot(w, a) + b
            c_values.append(c)
            a = ReLU(c)
            a_values.append(a)
        c = np.dot(self.weights[-1], a) + self.biases[-1]
        c_values.append(c)
        a_values.append(c)

        # Calculate partial derivative dynamically
        partial_ws = [np.zeros(w.shape) for w in self.weights]
        partial_bs = [np.zeros(b.shape) for b in self.biases]
        delta = d_L2Loss(a_values[-1], y)
        partial_bs[-1] = delta
        partial_ws[-1] = np.dot(delta, a_values[-2].T)

        for l in range(2, len(self.weights) + 1):  # propagate the derivative using the chain rule
            c_l = c_values[-l]
            delta = np.dot(self.weights[-l + 1].T, delta) * d_ReLU(c_l)
            partial_bs[-l] = delta
            partial_ws[-l] = np.dot(delta, a_values[-l - 1].T)
        return partial_ws, partial_bs, L2Loss(a_values[-1], y)

    def evaluate_test(self, test):
        loss = 0
        for x, y in test:
            loss += L2Loss(self.forward(x), y)
        return loss / len(test)

    def average_weights(self):
        """
        :return: calculate the norm of each layer
        """
        return [(np.linalg.norm(w), np.linalg.norm(b)) for w, b in zip(self.weights, self.biases)]

    def predict(self, xs):
        return np.array([self.forward(x).squeeze(axis=-1) for x in xs])
