# Copyright 2018-2020 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This module contains the TensorFlowBox implementation of the TensorBox API.
"""
import tensorflow as tf


try:
    from tensorflow.python.eager.tape import should_record_backprop
except ImportError:  # pragma: no cover
    from tensorflow.python.eager.tape import should_record as should_record_backprop


import pennylane as qml


wrap_output = qml.proc.wrap_output


class TensorFlowBox(qml.proc.TensorBox):
    """Implements the :class:`~.TensorBox` API for TensorFlow tensors.

    For more details, please refer to the :class:`~.TensorBox` documentation.
    """

    abs = wrap_output(lambda self: tf.abs(self.data))
    angle = wrap_output(lambda self: tf.math.angle(self.data))
    arcsin = wrap_output(lambda self: tf.math.asin(self.data))
    cast = wrap_output(lambda self, dtype: tf.cast(self.data, dtype))
    expand_dims = wrap_output(lambda self, axis: tf.expand_dims(self.data, axis=axis))
    ones_like = wrap_output(lambda self: tf.ones_like(self.data))
    sqrt = wrap_output(lambda self: tf.sqrt(self.data))
    sum = wrap_output(
        lambda self, axis, keepdims: tf.reduce_sum(self.data, axis=axis, keepdims=keepdims)
    )
    T = wrap_output(lambda self: tf.transpose(self.data))
    take = wrap_output(lambda self, indices, axis=None: tf.gather(self.data, indices, axis=axis))

    def __len__(self):
        if isinstance(self.data, tf.Variable):
            return len(tf.convert_to_tensor(self.data))

        return super().__len__()

    @staticmethod
    def astensor(tensor):
        return tf.convert_to_tensor(tensor)

    @staticmethod
    def _coerce_types(tensors):
        dtypes = {i.dtype for i in tensors}

        if len(dtypes) == 1:
            return tensors

        complex_type = dtypes.intersection({tf.complex64, tf.complex128})
        float_type = dtypes.intersection({tf.float16, tf.float32, tf.float64})
        int_type = dtypes.intersection({tf.int8, tf.int16, tf.int32, tf.int64})

        cast_type = complex_type or float_type or int_type
        cast_type = list(cast_type)[-1]

        return [tf.cast(t, cast_type) for t in tensors]

    @staticmethod
    @wrap_output
    def concatenate(values, axis=0):
        if axis is None:
            # flatten and then concatenate zero'th dimension
            # to reproduce numpy's behaviour
            tensors = [
                tf.reshape(TensorFlowBox.astensor(t), [-1])
                for t in TensorFlowBox.unbox_list(tensors)
            ]
            tensors = TensorFlowBox._coerce_types([x, y])
            return tf.concat(tensors, axis=0)

        return tf.concat(TensorFlowBox.unbox_list(values), axis=axis)

    @staticmethod
    @wrap_output
    def dot(x, y):
        x, y = [TensorFlowBox.astensor(t) for t in TensorFlowBox.unbox_list([x, y])]
        x, y = TensorFlowBox._coerce_types([x, y])

        if x.ndim == 0 and y.ndim == 0:
            return x * y

        if x.ndim == 2 and y.ndim == 1:
            return tf.tensordot(x, y, axes=[[-1], [0]])

        if x.ndim == 2 and y.ndim == 2:
            return x @ y

        return tf.tensordot(x, y, axes=[[-1], [-2]])

    @property
    def interface(self):
        return "tf"

    def numpy(self):
        return self.data.numpy()

    @property
    def requires_grad(self):
        return should_record_backprop([self.astensor(self.data)])

    @property
    def shape(self):
        return tuple(self.data.shape)

    @staticmethod
    @wrap_output
    def stack(values, axis=0):
        values = TensorFlowBox._coerce_types(TensorFlowBox.unbox_list(values))
        res = tf.stack(values, axis=axis)
        return res

    @staticmethod
    @wrap_output
    def where(condition, x, y):
        return tf.where(TensorFlowBox.astensor(condition), *TensorFlowBox.unbox_list([x, y]))