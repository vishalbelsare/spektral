import tensorflow as tf
from tensorflow.keras import activations
from tensorflow.keras.layers import BatchNormalization, Dense
from tensorflow.keras.models import Sequential

from spektral.layers import ops
from spektral.layers.convolutional.message_passing import MessagePassing


class GINConv(MessagePassing):
    r"""
    A Graph Isomorphism Network (GIN) from the paper

    > [How Powerful are Graph Neural Networks?](https://arxiv.org/abs/1810.00826)<br>
    > Keyulu Xu et al.

    **Mode**: single, disjoint, mixed.

    **This layer expects a sparse adjacency matrix.**

    This layer computes for each node \(i\):
    $$
        \x_i' = \textrm{MLP}\big( (1 + \epsilon) \cdot \x_i + \sum\limits_{j
        \in \mathcal{N}(i)} \x_j \big)
    $$
    where \(\textrm{MLP}\) is a multi-layer perceptron.

    **Input**

    - Node features of shape `(n_nodes, n_node_features)`;
    - Binary adjacency matrix of shape `(n_nodes, n_nodes)`.

    **Output**

    - Node features with the same shape of the input, but the last dimension
    changed to `channels`.

    **Arguments**

    - `channels`: integer, number of output channels;
    - `epsilon`: unnamed parameter, see the original paper and the equation
    above.
    By setting `epsilon=None`, the parameter will be learned (default behaviour).
    If given as a value, the parameter will stay fixed.
    - `mlp_hidden`: list of integers, number of hidden units for each hidden
    layer in the MLP (if None, the MLP has only the output layer);
    - `mlp_activation`: activation for the MLP layers;
    - `mlp_batchnorm`: apply batch normalization after every hidden layer of the MLP;
    - `activation`: activation function;
    - `use_bias`: bool, add a bias vector to the output;
    - `kernel_initializer`: initializer for the weights;
    - `bias_initializer`: initializer for the bias vector;
    - `kernel_regularizer`: regularization applied to the weights;
    - `bias_regularizer`: regularization applied to the bias vector;
    - `activity_regularizer`: regularization applied to the output;
    - `kernel_constraint`: constraint applied to the weights;
    - `bias_constraint`: constraint applied to the bias vector.
    """

    def __init__(
        self,
        channels,
        epsilon=None,
        mlp_hidden=None,
        mlp_activation="relu",
        mlp_batchnorm=True,
        aggregate="sum",
        activation=None,
        use_bias=True,
        kernel_initializer="glorot_uniform",
        bias_initializer="zeros",
        kernel_regularizer=None,
        bias_regularizer=None,
        activity_regularizer=None,
        kernel_constraint=None,
        bias_constraint=None,
        **kwargs,
    ):
        super().__init__(
            aggregate=aggregate,
            activation=activation,
            use_bias=use_bias,
            kernel_initializer=kernel_initializer,
            bias_initializer=bias_initializer,
            kernel_regularizer=kernel_regularizer,
            bias_regularizer=bias_regularizer,
            activity_regularizer=activity_regularizer,
            kernel_constraint=kernel_constraint,
            bias_constraint=bias_constraint,
            **kwargs,
        )
        self.channels = channels
        self.epsilon = epsilon
        self.mlp_hidden = mlp_hidden if mlp_hidden else []
        self.mlp_activation = activations.get(mlp_activation)
        self.mlp_batchnorm = mlp_batchnorm

    def build(self, input_shape):
        assert len(input_shape) >= 2
        layer_kwargs = dict(
            kernel_initializer=self.kernel_initializer,
            bias_initializer=self.bias_initializer,
            kernel_regularizer=self.kernel_regularizer,
            bias_regularizer=self.bias_regularizer,
            kernel_constraint=self.kernel_constraint,
            bias_constraint=self.bias_constraint,
        )

        self.mlp = Sequential()
        for channels in self.mlp_hidden:
            self.mlp.add(Dense(channels, self.mlp_activation, **layer_kwargs))
            if self.mlp_batchnorm:
                self.mlp.add(BatchNormalization())
        self.mlp.add(
            Dense(
                self.channels, self.activation, use_bias=self.use_bias, **layer_kwargs
            )
        )

        if self.epsilon is None:
            self.eps = self.add_weight(shape=(1,), initializer="zeros", name="eps")
        else:
            # If epsilon is given, keep it constant
            self.eps = tf.cast(self.epsilon, self.dtype)
        self.one = tf.cast(1, self.dtype)

        self.built = True

    def call(self, inputs, **kwargs):
        x, a, _ = self.get_inputs(inputs)
        output = self.mlp((self.one + self.eps) * x + self.propagate(x, a))

        return output

    @property
    def config(self):
        return {
            "channels": self.channels,
            "epsilon": self.epsilon,
            "mlp_hidden": self.mlp_hidden,
            "mlp_activation": self.mlp_activation,
            "mlp_batchnorm": self.mlp_batchnorm,
        }


class GINConvBatch(GINConv):
    r"""
    A batch-mode version of GINConv.

    **Mode**: batch.

    **This layer expects a dense adjacency matrix.**
    """

    def call(self, inputs, **kwargs):
        x, a = inputs
        output = self.mlp((self.one + self.eps) * x + ops.modal_dot(a, x))

        return output
