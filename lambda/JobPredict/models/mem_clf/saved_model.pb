��

��
B
AssignVariableOp
resource
value"dtype"
dtypetype�
~
BiasAdd

value"T	
bias"T
output"T" 
Ttype:
2	"-
data_formatstringNHWC:
NHWCNCHW
8
Const
output"dtype"
valuetensor"
dtypetype
.
Identity

input"T
output"T"	
Ttype
q
MatMul
a"T
b"T
product"T"
transpose_abool( "
transpose_bbool( "
Ttype:

2	
e
MergeV2Checkpoints
checkpoint_prefixes
destination_prefix"
delete_old_dirsbool(�

NoOp
M
Pack
values"T*N
output"T"
Nint(0"	
Ttype"
axisint 
C
Placeholder
output"dtype"
dtypetype"
shapeshape:
@
ReadVariableOp
resource
value"dtype"
dtypetype�
E
Relu
features"T
activations"T"
Ttype:
2	
o
	RestoreV2

prefix
tensor_names
shape_and_slices
tensors2dtypes"
dtypes
list(type)(0�
l
SaveV2

prefix
tensor_names
shape_and_slices
tensors2dtypes"
dtypes
list(type)(0�
?
Select
	condition

t"T
e"T
output"T"	
Ttype
H
ShardedFilename
basename	
shard

num_shards
filename
9
Softmax
logits"T
softmax"T"
Ttype:
2
�
StatefulPartitionedCall
args2Tin
output2Tout"
Tin
list(type)("
Tout
list(type)("	
ffunc"
configstring "
config_protostring "
executor_typestring �
@
StaticRegexFullMatch	
input

output
"
patternstring
N

StringJoin
inputs*N

output"
Nint(0"
	separatorstring 
�
VarHandleOp
resource"
	containerstring "
shared_namestring "
dtypetype"
shapeshape"#
allowed_deviceslist(string)
 �"serve*2.6.22v2.6.1-9-gc2363d6d0258°	
|
1_dense18/kernelVarHandleOp*
_output_shapes
: *
dtype0*
shape
:	*!
shared_name1_dense18/kernel
u
$1_dense18/kernel/Read/ReadVariableOpReadVariableOp1_dense18/kernel*
_output_shapes

:	*
dtype0
t
1_dense18/biasVarHandleOp*
_output_shapes
: *
dtype0*
shape:*
shared_name1_dense18/bias
m
"1_dense18/bias/Read/ReadVariableOpReadVariableOp1_dense18/bias*
_output_shapes
:*
dtype0
|
2_dense32/kernelVarHandleOp*
_output_shapes
: *
dtype0*
shape
: *!
shared_name2_dense32/kernel
u
$2_dense32/kernel/Read/ReadVariableOpReadVariableOp2_dense32/kernel*
_output_shapes

: *
dtype0
t
2_dense32/biasVarHandleOp*
_output_shapes
: *
dtype0*
shape: *
shared_name2_dense32/bias
m
"2_dense32/bias/Read/ReadVariableOpReadVariableOp2_dense32/bias*
_output_shapes
: *
dtype0
|
3_dense64/kernelVarHandleOp*
_output_shapes
: *
dtype0*
shape
: @*!
shared_name3_dense64/kernel
u
$3_dense64/kernel/Read/ReadVariableOpReadVariableOp3_dense64/kernel*
_output_shapes

: @*
dtype0
t
3_dense64/biasVarHandleOp*
_output_shapes
: *
dtype0*
shape:@*
shared_name3_dense64/bias
m
"3_dense64/bias/Read/ReadVariableOpReadVariableOp3_dense64/bias*
_output_shapes
:@*
dtype0
|
4_dense32/kernelVarHandleOp*
_output_shapes
: *
dtype0*
shape
:@ *!
shared_name4_dense32/kernel
u
$4_dense32/kernel/Read/ReadVariableOpReadVariableOp4_dense32/kernel*
_output_shapes

:@ *
dtype0
t
4_dense32/biasVarHandleOp*
_output_shapes
: *
dtype0*
shape: *
shared_name4_dense32/bias
m
"4_dense32/bias/Read/ReadVariableOpReadVariableOp4_dense32/bias*
_output_shapes
: *
dtype0
|
5_dense18/kernelVarHandleOp*
_output_shapes
: *
dtype0*
shape
: *!
shared_name5_dense18/kernel
u
$5_dense18/kernel/Read/ReadVariableOpReadVariableOp5_dense18/kernel*
_output_shapes

: *
dtype0
t
5_dense18/biasVarHandleOp*
_output_shapes
: *
dtype0*
shape:*
shared_name5_dense18/bias
m
"5_dense18/bias/Read/ReadVariableOpReadVariableOp5_dense18/bias*
_output_shapes
:*
dtype0
z
6_dense9/kernelVarHandleOp*
_output_shapes
: *
dtype0*
shape
:	* 
shared_name6_dense9/kernel
s
#6_dense9/kernel/Read/ReadVariableOpReadVariableOp6_dense9/kernel*
_output_shapes

:	*
dtype0
r
6_dense9/biasVarHandleOp*
_output_shapes
: *
dtype0*
shape:	*
shared_name6_dense9/bias
k
!6_dense9/bias/Read/ReadVariableOpReadVariableOp6_dense9/bias*
_output_shapes
:	*
dtype0
�
output_mem_clf/kernelVarHandleOp*
_output_shapes
: *
dtype0*
shape
:	*&
shared_nameoutput_mem_clf/kernel

)output_mem_clf/kernel/Read/ReadVariableOpReadVariableOpoutput_mem_clf/kernel*
_output_shapes

:	*
dtype0
~
output_mem_clf/biasVarHandleOp*
_output_shapes
: *
dtype0*
shape:*$
shared_nameoutput_mem_clf/bias
w
'output_mem_clf/bias/Read/ReadVariableOpReadVariableOpoutput_mem_clf/bias*
_output_shapes
:*
dtype0
f
	Adam/iterVarHandleOp*
_output_shapes
: *
dtype0	*
shape: *
shared_name	Adam/iter
_
Adam/iter/Read/ReadVariableOpReadVariableOp	Adam/iter*
_output_shapes
: *
dtype0	
j
Adam/beta_1VarHandleOp*
_output_shapes
: *
dtype0*
shape: *
shared_nameAdam/beta_1
c
Adam/beta_1/Read/ReadVariableOpReadVariableOpAdam/beta_1*
_output_shapes
: *
dtype0
j
Adam/beta_2VarHandleOp*
_output_shapes
: *
dtype0*
shape: *
shared_nameAdam/beta_2
c
Adam/beta_2/Read/ReadVariableOpReadVariableOpAdam/beta_2*
_output_shapes
: *
dtype0
h

Adam/decayVarHandleOp*
_output_shapes
: *
dtype0*
shape: *
shared_name
Adam/decay
a
Adam/decay/Read/ReadVariableOpReadVariableOp
Adam/decay*
_output_shapes
: *
dtype0
x
Adam/learning_rateVarHandleOp*
_output_shapes
: *
dtype0*
shape: *#
shared_nameAdam/learning_rate
q
&Adam/learning_rate/Read/ReadVariableOpReadVariableOpAdam/learning_rate*
_output_shapes
: *
dtype0
^
totalVarHandleOp*
_output_shapes
: *
dtype0*
shape: *
shared_nametotal
W
total/Read/ReadVariableOpReadVariableOptotal*
_output_shapes
: *
dtype0
^
countVarHandleOp*
_output_shapes
: *
dtype0*
shape: *
shared_namecount
W
count/Read/ReadVariableOpReadVariableOpcount*
_output_shapes
: *
dtype0
b
total_1VarHandleOp*
_output_shapes
: *
dtype0*
shape: *
shared_name	total_1
[
total_1/Read/ReadVariableOpReadVariableOptotal_1*
_output_shapes
: *
dtype0
b
count_1VarHandleOp*
_output_shapes
: *
dtype0*
shape: *
shared_name	count_1
[
count_1/Read/ReadVariableOpReadVariableOpcount_1*
_output_shapes
: *
dtype0
�
Adam/1_dense18/kernel/mVarHandleOp*
_output_shapes
: *
dtype0*
shape
:	*(
shared_nameAdam/1_dense18/kernel/m
�
+Adam/1_dense18/kernel/m/Read/ReadVariableOpReadVariableOpAdam/1_dense18/kernel/m*
_output_shapes

:	*
dtype0
�
Adam/1_dense18/bias/mVarHandleOp*
_output_shapes
: *
dtype0*
shape:*&
shared_nameAdam/1_dense18/bias/m
{
)Adam/1_dense18/bias/m/Read/ReadVariableOpReadVariableOpAdam/1_dense18/bias/m*
_output_shapes
:*
dtype0
�
Adam/2_dense32/kernel/mVarHandleOp*
_output_shapes
: *
dtype0*
shape
: *(
shared_nameAdam/2_dense32/kernel/m
�
+Adam/2_dense32/kernel/m/Read/ReadVariableOpReadVariableOpAdam/2_dense32/kernel/m*
_output_shapes

: *
dtype0
�
Adam/2_dense32/bias/mVarHandleOp*
_output_shapes
: *
dtype0*
shape: *&
shared_nameAdam/2_dense32/bias/m
{
)Adam/2_dense32/bias/m/Read/ReadVariableOpReadVariableOpAdam/2_dense32/bias/m*
_output_shapes
: *
dtype0
�
Adam/3_dense64/kernel/mVarHandleOp*
_output_shapes
: *
dtype0*
shape
: @*(
shared_nameAdam/3_dense64/kernel/m
�
+Adam/3_dense64/kernel/m/Read/ReadVariableOpReadVariableOpAdam/3_dense64/kernel/m*
_output_shapes

: @*
dtype0
�
Adam/3_dense64/bias/mVarHandleOp*
_output_shapes
: *
dtype0*
shape:@*&
shared_nameAdam/3_dense64/bias/m
{
)Adam/3_dense64/bias/m/Read/ReadVariableOpReadVariableOpAdam/3_dense64/bias/m*
_output_shapes
:@*
dtype0
�
Adam/4_dense32/kernel/mVarHandleOp*
_output_shapes
: *
dtype0*
shape
:@ *(
shared_nameAdam/4_dense32/kernel/m
�
+Adam/4_dense32/kernel/m/Read/ReadVariableOpReadVariableOpAdam/4_dense32/kernel/m*
_output_shapes

:@ *
dtype0
�
Adam/4_dense32/bias/mVarHandleOp*
_output_shapes
: *
dtype0*
shape: *&
shared_nameAdam/4_dense32/bias/m
{
)Adam/4_dense32/bias/m/Read/ReadVariableOpReadVariableOpAdam/4_dense32/bias/m*
_output_shapes
: *
dtype0
�
Adam/5_dense18/kernel/mVarHandleOp*
_output_shapes
: *
dtype0*
shape
: *(
shared_nameAdam/5_dense18/kernel/m
�
+Adam/5_dense18/kernel/m/Read/ReadVariableOpReadVariableOpAdam/5_dense18/kernel/m*
_output_shapes

: *
dtype0
�
Adam/5_dense18/bias/mVarHandleOp*
_output_shapes
: *
dtype0*
shape:*&
shared_nameAdam/5_dense18/bias/m
{
)Adam/5_dense18/bias/m/Read/ReadVariableOpReadVariableOpAdam/5_dense18/bias/m*
_output_shapes
:*
dtype0
�
Adam/6_dense9/kernel/mVarHandleOp*
_output_shapes
: *
dtype0*
shape
:	*'
shared_nameAdam/6_dense9/kernel/m
�
*Adam/6_dense9/kernel/m/Read/ReadVariableOpReadVariableOpAdam/6_dense9/kernel/m*
_output_shapes

:	*
dtype0
�
Adam/6_dense9/bias/mVarHandleOp*
_output_shapes
: *
dtype0*
shape:	*%
shared_nameAdam/6_dense9/bias/m
y
(Adam/6_dense9/bias/m/Read/ReadVariableOpReadVariableOpAdam/6_dense9/bias/m*
_output_shapes
:	*
dtype0
�
Adam/output_mem_clf/kernel/mVarHandleOp*
_output_shapes
: *
dtype0*
shape
:	*-
shared_nameAdam/output_mem_clf/kernel/m
�
0Adam/output_mem_clf/kernel/m/Read/ReadVariableOpReadVariableOpAdam/output_mem_clf/kernel/m*
_output_shapes

:	*
dtype0
�
Adam/output_mem_clf/bias/mVarHandleOp*
_output_shapes
: *
dtype0*
shape:*+
shared_nameAdam/output_mem_clf/bias/m
�
.Adam/output_mem_clf/bias/m/Read/ReadVariableOpReadVariableOpAdam/output_mem_clf/bias/m*
_output_shapes
:*
dtype0
�
Adam/1_dense18/kernel/vVarHandleOp*
_output_shapes
: *
dtype0*
shape
:	*(
shared_nameAdam/1_dense18/kernel/v
�
+Adam/1_dense18/kernel/v/Read/ReadVariableOpReadVariableOpAdam/1_dense18/kernel/v*
_output_shapes

:	*
dtype0
�
Adam/1_dense18/bias/vVarHandleOp*
_output_shapes
: *
dtype0*
shape:*&
shared_nameAdam/1_dense18/bias/v
{
)Adam/1_dense18/bias/v/Read/ReadVariableOpReadVariableOpAdam/1_dense18/bias/v*
_output_shapes
:*
dtype0
�
Adam/2_dense32/kernel/vVarHandleOp*
_output_shapes
: *
dtype0*
shape
: *(
shared_nameAdam/2_dense32/kernel/v
�
+Adam/2_dense32/kernel/v/Read/ReadVariableOpReadVariableOpAdam/2_dense32/kernel/v*
_output_shapes

: *
dtype0
�
Adam/2_dense32/bias/vVarHandleOp*
_output_shapes
: *
dtype0*
shape: *&
shared_nameAdam/2_dense32/bias/v
{
)Adam/2_dense32/bias/v/Read/ReadVariableOpReadVariableOpAdam/2_dense32/bias/v*
_output_shapes
: *
dtype0
�
Adam/3_dense64/kernel/vVarHandleOp*
_output_shapes
: *
dtype0*
shape
: @*(
shared_nameAdam/3_dense64/kernel/v
�
+Adam/3_dense64/kernel/v/Read/ReadVariableOpReadVariableOpAdam/3_dense64/kernel/v*
_output_shapes

: @*
dtype0
�
Adam/3_dense64/bias/vVarHandleOp*
_output_shapes
: *
dtype0*
shape:@*&
shared_nameAdam/3_dense64/bias/v
{
)Adam/3_dense64/bias/v/Read/ReadVariableOpReadVariableOpAdam/3_dense64/bias/v*
_output_shapes
:@*
dtype0
�
Adam/4_dense32/kernel/vVarHandleOp*
_output_shapes
: *
dtype0*
shape
:@ *(
shared_nameAdam/4_dense32/kernel/v
�
+Adam/4_dense32/kernel/v/Read/ReadVariableOpReadVariableOpAdam/4_dense32/kernel/v*
_output_shapes

:@ *
dtype0
�
Adam/4_dense32/bias/vVarHandleOp*
_output_shapes
: *
dtype0*
shape: *&
shared_nameAdam/4_dense32/bias/v
{
)Adam/4_dense32/bias/v/Read/ReadVariableOpReadVariableOpAdam/4_dense32/bias/v*
_output_shapes
: *
dtype0
�
Adam/5_dense18/kernel/vVarHandleOp*
_output_shapes
: *
dtype0*
shape
: *(
shared_nameAdam/5_dense18/kernel/v
�
+Adam/5_dense18/kernel/v/Read/ReadVariableOpReadVariableOpAdam/5_dense18/kernel/v*
_output_shapes

: *
dtype0
�
Adam/5_dense18/bias/vVarHandleOp*
_output_shapes
: *
dtype0*
shape:*&
shared_nameAdam/5_dense18/bias/v
{
)Adam/5_dense18/bias/v/Read/ReadVariableOpReadVariableOpAdam/5_dense18/bias/v*
_output_shapes
:*
dtype0
�
Adam/6_dense9/kernel/vVarHandleOp*
_output_shapes
: *
dtype0*
shape
:	*'
shared_nameAdam/6_dense9/kernel/v
�
*Adam/6_dense9/kernel/v/Read/ReadVariableOpReadVariableOpAdam/6_dense9/kernel/v*
_output_shapes

:	*
dtype0
�
Adam/6_dense9/bias/vVarHandleOp*
_output_shapes
: *
dtype0*
shape:	*%
shared_nameAdam/6_dense9/bias/v
y
(Adam/6_dense9/bias/v/Read/ReadVariableOpReadVariableOpAdam/6_dense9/bias/v*
_output_shapes
:	*
dtype0
�
Adam/output_mem_clf/kernel/vVarHandleOp*
_output_shapes
: *
dtype0*
shape
:	*-
shared_nameAdam/output_mem_clf/kernel/v
�
0Adam/output_mem_clf/kernel/v/Read/ReadVariableOpReadVariableOpAdam/output_mem_clf/kernel/v*
_output_shapes

:	*
dtype0
�
Adam/output_mem_clf/bias/vVarHandleOp*
_output_shapes
: *
dtype0*
shape:*+
shared_nameAdam/output_mem_clf/bias/v
�
.Adam/output_mem_clf/bias/v/Read/ReadVariableOpReadVariableOpAdam/output_mem_clf/bias/v*
_output_shapes
:*
dtype0

NoOpNoOp
�I
ConstConst"/device:CPU:0*
_output_shapes
: *
dtype0*�H
value�HB�H B�H
�
layer-0
layer_with_weights-0
layer-1
layer_with_weights-1
layer-2
layer_with_weights-2
layer-3
layer_with_weights-3
layer-4
layer_with_weights-4
layer-5
layer_with_weights-5
layer-6
layer_with_weights-6
layer-7
		optimizer

trainable_variables
regularization_losses
	variables
	keras_api

signatures
 
h

kernel
bias
trainable_variables
regularization_losses
	variables
	keras_api
h

kernel
bias
trainable_variables
regularization_losses
	variables
	keras_api
h

kernel
bias
trainable_variables
regularization_losses
	variables
 	keras_api
h

!kernel
"bias
#trainable_variables
$regularization_losses
%	variables
&	keras_api
h

'kernel
(bias
)trainable_variables
*regularization_losses
+	variables
,	keras_api
h

-kernel
.bias
/trainable_variables
0regularization_losses
1	variables
2	keras_api
h

3kernel
4bias
5trainable_variables
6regularization_losses
7	variables
8	keras_api
�
9iter

:beta_1

;beta_2
	<decay
=learning_ratemqmrmsmtmumv!mw"mx'my(mz-m{.m|3m}4m~vv�v�v�v�v�!v�"v�'v�(v�-v�.v�3v�4v�
f
0
1
2
3
4
5
!6
"7
'8
(9
-10
.11
312
413
 
f
0
1
2
3
4
5
!6
"7
'8
(9
-10
.11
312
413
�

trainable_variables
>non_trainable_variables
?layer_metrics
@metrics
regularization_losses

Alayers
	variables
Blayer_regularization_losses
 
\Z
VARIABLE_VALUE1_dense18/kernel6layer_with_weights-0/kernel/.ATTRIBUTES/VARIABLE_VALUE
XV
VARIABLE_VALUE1_dense18/bias4layer_with_weights-0/bias/.ATTRIBUTES/VARIABLE_VALUE

0
1
 

0
1
�
trainable_variables
Cnon_trainable_variables
Dlayer_metrics
Emetrics
regularization_losses

Flayers
	variables
Glayer_regularization_losses
\Z
VARIABLE_VALUE2_dense32/kernel6layer_with_weights-1/kernel/.ATTRIBUTES/VARIABLE_VALUE
XV
VARIABLE_VALUE2_dense32/bias4layer_with_weights-1/bias/.ATTRIBUTES/VARIABLE_VALUE

0
1
 

0
1
�
trainable_variables
Hnon_trainable_variables
Ilayer_metrics
Jmetrics
regularization_losses

Klayers
	variables
Llayer_regularization_losses
\Z
VARIABLE_VALUE3_dense64/kernel6layer_with_weights-2/kernel/.ATTRIBUTES/VARIABLE_VALUE
XV
VARIABLE_VALUE3_dense64/bias4layer_with_weights-2/bias/.ATTRIBUTES/VARIABLE_VALUE

0
1
 

0
1
�
trainable_variables
Mnon_trainable_variables
Nlayer_metrics
Ometrics
regularization_losses

Players
	variables
Qlayer_regularization_losses
\Z
VARIABLE_VALUE4_dense32/kernel6layer_with_weights-3/kernel/.ATTRIBUTES/VARIABLE_VALUE
XV
VARIABLE_VALUE4_dense32/bias4layer_with_weights-3/bias/.ATTRIBUTES/VARIABLE_VALUE

!0
"1
 

!0
"1
�
#trainable_variables
Rnon_trainable_variables
Slayer_metrics
Tmetrics
$regularization_losses

Ulayers
%	variables
Vlayer_regularization_losses
\Z
VARIABLE_VALUE5_dense18/kernel6layer_with_weights-4/kernel/.ATTRIBUTES/VARIABLE_VALUE
XV
VARIABLE_VALUE5_dense18/bias4layer_with_weights-4/bias/.ATTRIBUTES/VARIABLE_VALUE

'0
(1
 

'0
(1
�
)trainable_variables
Wnon_trainable_variables
Xlayer_metrics
Ymetrics
*regularization_losses

Zlayers
+	variables
[layer_regularization_losses
[Y
VARIABLE_VALUE6_dense9/kernel6layer_with_weights-5/kernel/.ATTRIBUTES/VARIABLE_VALUE
WU
VARIABLE_VALUE6_dense9/bias4layer_with_weights-5/bias/.ATTRIBUTES/VARIABLE_VALUE

-0
.1
 

-0
.1
�
/trainable_variables
\non_trainable_variables
]layer_metrics
^metrics
0regularization_losses

_layers
1	variables
`layer_regularization_losses
a_
VARIABLE_VALUEoutput_mem_clf/kernel6layer_with_weights-6/kernel/.ATTRIBUTES/VARIABLE_VALUE
][
VARIABLE_VALUEoutput_mem_clf/bias4layer_with_weights-6/bias/.ATTRIBUTES/VARIABLE_VALUE

30
41
 

30
41
�
5trainable_variables
anon_trainable_variables
blayer_metrics
cmetrics
6regularization_losses

dlayers
7	variables
elayer_regularization_losses
HF
VARIABLE_VALUE	Adam/iter)optimizer/iter/.ATTRIBUTES/VARIABLE_VALUE
LJ
VARIABLE_VALUEAdam/beta_1+optimizer/beta_1/.ATTRIBUTES/VARIABLE_VALUE
LJ
VARIABLE_VALUEAdam/beta_2+optimizer/beta_2/.ATTRIBUTES/VARIABLE_VALUE
JH
VARIABLE_VALUE
Adam/decay*optimizer/decay/.ATTRIBUTES/VARIABLE_VALUE
ZX
VARIABLE_VALUEAdam/learning_rate2optimizer/learning_rate/.ATTRIBUTES/VARIABLE_VALUE
 
 

f0
g1
8
0
1
2
3
4
5
6
7
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
4
	htotal
	icount
j	variables
k	keras_api
D
	ltotal
	mcount
n
_fn_kwargs
o	variables
p	keras_api
OM
VARIABLE_VALUEtotal4keras_api/metrics/0/total/.ATTRIBUTES/VARIABLE_VALUE
OM
VARIABLE_VALUEcount4keras_api/metrics/0/count/.ATTRIBUTES/VARIABLE_VALUE

h0
i1

j	variables
QO
VARIABLE_VALUEtotal_14keras_api/metrics/1/total/.ATTRIBUTES/VARIABLE_VALUE
QO
VARIABLE_VALUEcount_14keras_api/metrics/1/count/.ATTRIBUTES/VARIABLE_VALUE
 

l0
m1

o	variables
}
VARIABLE_VALUEAdam/1_dense18/kernel/mRlayer_with_weights-0/kernel/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUE
{y
VARIABLE_VALUEAdam/1_dense18/bias/mPlayer_with_weights-0/bias/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUE
}
VARIABLE_VALUEAdam/2_dense32/kernel/mRlayer_with_weights-1/kernel/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUE
{y
VARIABLE_VALUEAdam/2_dense32/bias/mPlayer_with_weights-1/bias/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUE
}
VARIABLE_VALUEAdam/3_dense64/kernel/mRlayer_with_weights-2/kernel/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUE
{y
VARIABLE_VALUEAdam/3_dense64/bias/mPlayer_with_weights-2/bias/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUE
}
VARIABLE_VALUEAdam/4_dense32/kernel/mRlayer_with_weights-3/kernel/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUE
{y
VARIABLE_VALUEAdam/4_dense32/bias/mPlayer_with_weights-3/bias/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUE
}
VARIABLE_VALUEAdam/5_dense18/kernel/mRlayer_with_weights-4/kernel/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUE
{y
VARIABLE_VALUEAdam/5_dense18/bias/mPlayer_with_weights-4/bias/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUE
~|
VARIABLE_VALUEAdam/6_dense9/kernel/mRlayer_with_weights-5/kernel/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUE
zx
VARIABLE_VALUEAdam/6_dense9/bias/mPlayer_with_weights-5/bias/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUE
��
VARIABLE_VALUEAdam/output_mem_clf/kernel/mRlayer_with_weights-6/kernel/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUE
�~
VARIABLE_VALUEAdam/output_mem_clf/bias/mPlayer_with_weights-6/bias/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUE
}
VARIABLE_VALUEAdam/1_dense18/kernel/vRlayer_with_weights-0/kernel/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUE
{y
VARIABLE_VALUEAdam/1_dense18/bias/vPlayer_with_weights-0/bias/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUE
}
VARIABLE_VALUEAdam/2_dense32/kernel/vRlayer_with_weights-1/kernel/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUE
{y
VARIABLE_VALUEAdam/2_dense32/bias/vPlayer_with_weights-1/bias/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUE
}
VARIABLE_VALUEAdam/3_dense64/kernel/vRlayer_with_weights-2/kernel/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUE
{y
VARIABLE_VALUEAdam/3_dense64/bias/vPlayer_with_weights-2/bias/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUE
}
VARIABLE_VALUEAdam/4_dense32/kernel/vRlayer_with_weights-3/kernel/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUE
{y
VARIABLE_VALUEAdam/4_dense32/bias/vPlayer_with_weights-3/bias/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUE
}
VARIABLE_VALUEAdam/5_dense18/kernel/vRlayer_with_weights-4/kernel/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUE
{y
VARIABLE_VALUEAdam/5_dense18/bias/vPlayer_with_weights-4/bias/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUE
~|
VARIABLE_VALUEAdam/6_dense9/kernel/vRlayer_with_weights-5/kernel/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUE
zx
VARIABLE_VALUEAdam/6_dense9/bias/vPlayer_with_weights-5/bias/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUE
��
VARIABLE_VALUEAdam/output_mem_clf/kernel/vRlayer_with_weights-6/kernel/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUE
�~
VARIABLE_VALUEAdam/output_mem_clf/bias/vPlayer_with_weights-6/bias/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUE
{
serving_default_hst_jobsPlaceholder*'
_output_shapes
:���������	*
dtype0*
shape:���������	
�
StatefulPartitionedCallStatefulPartitionedCallserving_default_hst_jobs1_dense18/kernel1_dense18/bias2_dense32/kernel2_dense32/bias3_dense64/kernel3_dense64/bias4_dense32/kernel4_dense32/bias5_dense18/kernel5_dense18/bias6_dense9/kernel6_dense9/biasoutput_mem_clf/kerneloutput_mem_clf/bias*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������*0
_read_only_resource_inputs
	
*-
config_proto

CPU

GPU 2J 8� *-
f(R&
$__inference_signature_wrapper_925804
O
saver_filenamePlaceholder*
_output_shapes
: *
dtype0*
shape: 
�
StatefulPartitionedCall_1StatefulPartitionedCallsaver_filename$1_dense18/kernel/Read/ReadVariableOp"1_dense18/bias/Read/ReadVariableOp$2_dense32/kernel/Read/ReadVariableOp"2_dense32/bias/Read/ReadVariableOp$3_dense64/kernel/Read/ReadVariableOp"3_dense64/bias/Read/ReadVariableOp$4_dense32/kernel/Read/ReadVariableOp"4_dense32/bias/Read/ReadVariableOp$5_dense18/kernel/Read/ReadVariableOp"5_dense18/bias/Read/ReadVariableOp#6_dense9/kernel/Read/ReadVariableOp!6_dense9/bias/Read/ReadVariableOp)output_mem_clf/kernel/Read/ReadVariableOp'output_mem_clf/bias/Read/ReadVariableOpAdam/iter/Read/ReadVariableOpAdam/beta_1/Read/ReadVariableOpAdam/beta_2/Read/ReadVariableOpAdam/decay/Read/ReadVariableOp&Adam/learning_rate/Read/ReadVariableOptotal/Read/ReadVariableOpcount/Read/ReadVariableOptotal_1/Read/ReadVariableOpcount_1/Read/ReadVariableOp+Adam/1_dense18/kernel/m/Read/ReadVariableOp)Adam/1_dense18/bias/m/Read/ReadVariableOp+Adam/2_dense32/kernel/m/Read/ReadVariableOp)Adam/2_dense32/bias/m/Read/ReadVariableOp+Adam/3_dense64/kernel/m/Read/ReadVariableOp)Adam/3_dense64/bias/m/Read/ReadVariableOp+Adam/4_dense32/kernel/m/Read/ReadVariableOp)Adam/4_dense32/bias/m/Read/ReadVariableOp+Adam/5_dense18/kernel/m/Read/ReadVariableOp)Adam/5_dense18/bias/m/Read/ReadVariableOp*Adam/6_dense9/kernel/m/Read/ReadVariableOp(Adam/6_dense9/bias/m/Read/ReadVariableOp0Adam/output_mem_clf/kernel/m/Read/ReadVariableOp.Adam/output_mem_clf/bias/m/Read/ReadVariableOp+Adam/1_dense18/kernel/v/Read/ReadVariableOp)Adam/1_dense18/bias/v/Read/ReadVariableOp+Adam/2_dense32/kernel/v/Read/ReadVariableOp)Adam/2_dense32/bias/v/Read/ReadVariableOp+Adam/3_dense64/kernel/v/Read/ReadVariableOp)Adam/3_dense64/bias/v/Read/ReadVariableOp+Adam/4_dense32/kernel/v/Read/ReadVariableOp)Adam/4_dense32/bias/v/Read/ReadVariableOp+Adam/5_dense18/kernel/v/Read/ReadVariableOp)Adam/5_dense18/bias/v/Read/ReadVariableOp*Adam/6_dense9/kernel/v/Read/ReadVariableOp(Adam/6_dense9/bias/v/Read/ReadVariableOp0Adam/output_mem_clf/kernel/v/Read/ReadVariableOp.Adam/output_mem_clf/bias/v/Read/ReadVariableOpConst*@
Tin9
725	*
Tout
2*
_collective_manager_ids
 *
_output_shapes
: * 
_read_only_resource_inputs
 *-
config_proto

CPU

GPU 2J 8� *(
f#R!
__inference__traced_save_926292
�

StatefulPartitionedCall_2StatefulPartitionedCallsaver_filename1_dense18/kernel1_dense18/bias2_dense32/kernel2_dense32/bias3_dense64/kernel3_dense64/bias4_dense32/kernel4_dense32/bias5_dense18/kernel5_dense18/bias6_dense9/kernel6_dense9/biasoutput_mem_clf/kerneloutput_mem_clf/bias	Adam/iterAdam/beta_1Adam/beta_2
Adam/decayAdam/learning_ratetotalcounttotal_1count_1Adam/1_dense18/kernel/mAdam/1_dense18/bias/mAdam/2_dense32/kernel/mAdam/2_dense32/bias/mAdam/3_dense64/kernel/mAdam/3_dense64/bias/mAdam/4_dense32/kernel/mAdam/4_dense32/bias/mAdam/5_dense18/kernel/mAdam/5_dense18/bias/mAdam/6_dense9/kernel/mAdam/6_dense9/bias/mAdam/output_mem_clf/kernel/mAdam/output_mem_clf/bias/mAdam/1_dense18/kernel/vAdam/1_dense18/bias/vAdam/2_dense32/kernel/vAdam/2_dense32/bias/vAdam/3_dense64/kernel/vAdam/3_dense64/bias/vAdam/4_dense32/kernel/vAdam/4_dense32/bias/vAdam/5_dense18/kernel/vAdam/5_dense18/bias/vAdam/6_dense9/kernel/vAdam/6_dense9/bias/vAdam/output_mem_clf/kernel/vAdam/output_mem_clf/bias/v*?
Tin8
624*
Tout
2*
_collective_manager_ids
 *
_output_shapes
: * 
_read_only_resource_inputs
 *-
config_proto

CPU

GPU 2J 8� *+
f&R$
"__inference__traced_restore_926455��
�
�
)__inference_6_dense9_layer_call_fn_926096

inputs
unknown:	
	unknown_0:	
identity��StatefulPartitionedCall�
StatefulPartitionedCallStatefulPartitionedCallinputsunknown	unknown_0*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������	*$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *M
fHRF
D__inference_6_dense9_layer_call_and_return_conditional_losses_9254222
StatefulPartitionedCall{
IdentityIdentity StatefulPartitionedCall:output:0^NoOp*
T0*'
_output_shapes
:���������	2

Identityh
NoOpNoOp^StatefulPartitionedCall*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime**
_input_shapes
:���������: : 22
StatefulPartitionedCallStatefulPartitionedCall:O K
'
_output_shapes
:���������
 
_user_specified_nameinputs
�(
�
M__inference_memory_classifier_layer_call_and_return_conditional_losses_925621

inputs 
dense18_925585:	
dense18_925587: 
dense32_925590: 
dense32_925592:  
dense64_925595: @
dense64_925597:@ 
dense32_925600:@ 
dense32_925602:  
dense18_925605: 
dense18_925607:
dense9_925610:	
dense9_925612:	'
output_mem_clf_925615:	#
output_mem_clf_925617:
identity��!1_dense18/StatefulPartitionedCall�!2_dense32/StatefulPartitionedCall�!3_dense64/StatefulPartitionedCall�!4_dense32/StatefulPartitionedCall�!5_dense18/StatefulPartitionedCall� 6_dense9/StatefulPartitionedCall�&output_mem_clf/StatefulPartitionedCall�
!1_dense18/StatefulPartitionedCallStatefulPartitionedCallinputsdense18_925585dense18_925587*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������*$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *N
fIRG
E__inference_1_dense18_layer_call_and_return_conditional_losses_9253372#
!1_dense18/StatefulPartitionedCall�
!2_dense32/StatefulPartitionedCallStatefulPartitionedCall*1_dense18/StatefulPartitionedCall:output:0dense32_925590dense32_925592*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:��������� *$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *N
fIRG
E__inference_2_dense32_layer_call_and_return_conditional_losses_9253542#
!2_dense32/StatefulPartitionedCall�
!3_dense64/StatefulPartitionedCallStatefulPartitionedCall*2_dense32/StatefulPartitionedCall:output:0dense64_925595dense64_925597*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������@*$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *N
fIRG
E__inference_3_dense64_layer_call_and_return_conditional_losses_9253712#
!3_dense64/StatefulPartitionedCall�
!4_dense32/StatefulPartitionedCallStatefulPartitionedCall*3_dense64/StatefulPartitionedCall:output:0dense32_925600dense32_925602*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:��������� *$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *N
fIRG
E__inference_4_dense32_layer_call_and_return_conditional_losses_9253882#
!4_dense32/StatefulPartitionedCall�
!5_dense18/StatefulPartitionedCallStatefulPartitionedCall*4_dense32/StatefulPartitionedCall:output:0dense18_925605dense18_925607*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������*$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *N
fIRG
E__inference_5_dense18_layer_call_and_return_conditional_losses_9254052#
!5_dense18/StatefulPartitionedCall�
 6_dense9/StatefulPartitionedCallStatefulPartitionedCall*5_dense18/StatefulPartitionedCall:output:0dense9_925610dense9_925612*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������	*$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *M
fHRF
D__inference_6_dense9_layer_call_and_return_conditional_losses_9254222"
 6_dense9/StatefulPartitionedCall�
&output_mem_clf/StatefulPartitionedCallStatefulPartitionedCall)6_dense9/StatefulPartitionedCall:output:0output_mem_clf_925615output_mem_clf_925617*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������*$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *S
fNRL
J__inference_output_mem_clf_layer_call_and_return_conditional_losses_9254392(
&output_mem_clf/StatefulPartitionedCall�
IdentityIdentity/output_mem_clf/StatefulPartitionedCall:output:0^NoOp*
T0*'
_output_shapes
:���������2

Identity�
NoOpNoOp"^1_dense18/StatefulPartitionedCall"^2_dense32/StatefulPartitionedCall"^3_dense64/StatefulPartitionedCall"^4_dense32/StatefulPartitionedCall"^5_dense18/StatefulPartitionedCall!^6_dense9/StatefulPartitionedCall'^output_mem_clf/StatefulPartitionedCall*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime*B
_input_shapes1
/:���������	: : : : : : : : : : : : : : 2F
!1_dense18/StatefulPartitionedCall!1_dense18/StatefulPartitionedCall2F
!2_dense32/StatefulPartitionedCall!2_dense32/StatefulPartitionedCall2F
!3_dense64/StatefulPartitionedCall!3_dense64/StatefulPartitionedCall2F
!4_dense32/StatefulPartitionedCall!4_dense32/StatefulPartitionedCall2F
!5_dense18/StatefulPartitionedCall!5_dense18/StatefulPartitionedCall2D
 6_dense9/StatefulPartitionedCall 6_dense9/StatefulPartitionedCall2P
&output_mem_clf/StatefulPartitionedCall&output_mem_clf/StatefulPartitionedCall:O K
'
_output_shapes
:���������	
 
_user_specified_nameinputs
�
�
E__inference_4_dense32_layer_call_and_return_conditional_losses_925388

inputs0
matmul_readvariableop_resource:@ -
biasadd_readvariableop_resource: 
identity��BiasAdd/ReadVariableOp�MatMul/ReadVariableOp�
MatMul/ReadVariableOpReadVariableOpmatmul_readvariableop_resource*
_output_shapes

:@ *
dtype02
MatMul/ReadVariableOps
MatMulMatMulinputsMatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:��������� 2
MatMul�
BiasAdd/ReadVariableOpReadVariableOpbiasadd_readvariableop_resource*
_output_shapes
: *
dtype02
BiasAdd/ReadVariableOp�
BiasAddBiasAddMatMul:product:0BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:��������� 2	
BiasAddX
ReluReluBiasAdd:output:0*
T0*'
_output_shapes
:��������� 2
Relum
IdentityIdentityRelu:activations:0^NoOp*
T0*'
_output_shapes
:��������� 2

Identity
NoOpNoOp^BiasAdd/ReadVariableOp^MatMul/ReadVariableOp*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime**
_input_shapes
:���������@: : 20
BiasAdd/ReadVariableOpBiasAdd/ReadVariableOp2.
MatMul/ReadVariableOpMatMul/ReadVariableOp:O K
'
_output_shapes
:���������@
 
_user_specified_nameinputs
�F
�
M__inference_memory_classifier_layer_call_and_return_conditional_losses_925857

inputs8
&dense18_matmul_readvariableop_resource:	5
'dense18_biasadd_readvariableop_resource:8
&dense32_matmul_readvariableop_resource: 5
'dense32_biasadd_readvariableop_resource: 8
&dense64_matmul_readvariableop_resource: @5
'dense64_biasadd_readvariableop_resource:@:
(dense32_matmul_readvariableop_resource_0:@ 7
)dense32_biasadd_readvariableop_resource_0: :
(dense18_matmul_readvariableop_resource_0: 7
)dense18_biasadd_readvariableop_resource_0:7
%dense9_matmul_readvariableop_resource:	4
&dense9_biasadd_readvariableop_resource:	?
-output_mem_clf_matmul_readvariableop_resource:	<
.output_mem_clf_biasadd_readvariableop_resource:
identity�� 1_dense18/BiasAdd/ReadVariableOp�1_dense18/MatMul/ReadVariableOp� 2_dense32/BiasAdd/ReadVariableOp�2_dense32/MatMul/ReadVariableOp� 3_dense64/BiasAdd/ReadVariableOp�3_dense64/MatMul/ReadVariableOp� 4_dense32/BiasAdd/ReadVariableOp�4_dense32/MatMul/ReadVariableOp� 5_dense18/BiasAdd/ReadVariableOp�5_dense18/MatMul/ReadVariableOp�6_dense9/BiasAdd/ReadVariableOp�6_dense9/MatMul/ReadVariableOp�%output_mem_clf/BiasAdd/ReadVariableOp�$output_mem_clf/MatMul/ReadVariableOp�
1_dense18/MatMul/ReadVariableOpReadVariableOp&dense18_matmul_readvariableop_resource*
_output_shapes

:	*
dtype02!
1_dense18/MatMul/ReadVariableOp�
1_dense18/MatMulMatMulinputs'1_dense18/MatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2
1_dense18/MatMul�
 1_dense18/BiasAdd/ReadVariableOpReadVariableOp'dense18_biasadd_readvariableop_resource*
_output_shapes
:*
dtype02"
 1_dense18/BiasAdd/ReadVariableOp�
1_dense18/BiasAddBiasAdd1_dense18/MatMul:product:0(1_dense18/BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2
1_dense18/BiasAddv
1_dense18/ReluRelu1_dense18/BiasAdd:output:0*
T0*'
_output_shapes
:���������2
1_dense18/Relu�
2_dense32/MatMul/ReadVariableOpReadVariableOp&dense32_matmul_readvariableop_resource*
_output_shapes

: *
dtype02!
2_dense32/MatMul/ReadVariableOp�
2_dense32/MatMulMatMul1_dense18/Relu:activations:0'2_dense32/MatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:��������� 2
2_dense32/MatMul�
 2_dense32/BiasAdd/ReadVariableOpReadVariableOp'dense32_biasadd_readvariableop_resource*
_output_shapes
: *
dtype02"
 2_dense32/BiasAdd/ReadVariableOp�
2_dense32/BiasAddBiasAdd2_dense32/MatMul:product:0(2_dense32/BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:��������� 2
2_dense32/BiasAddv
2_dense32/ReluRelu2_dense32/BiasAdd:output:0*
T0*'
_output_shapes
:��������� 2
2_dense32/Relu�
3_dense64/MatMul/ReadVariableOpReadVariableOp&dense64_matmul_readvariableop_resource*
_output_shapes

: @*
dtype02!
3_dense64/MatMul/ReadVariableOp�
3_dense64/MatMulMatMul2_dense32/Relu:activations:0'3_dense64/MatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������@2
3_dense64/MatMul�
 3_dense64/BiasAdd/ReadVariableOpReadVariableOp'dense64_biasadd_readvariableop_resource*
_output_shapes
:@*
dtype02"
 3_dense64/BiasAdd/ReadVariableOp�
3_dense64/BiasAddBiasAdd3_dense64/MatMul:product:0(3_dense64/BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������@2
3_dense64/BiasAddv
3_dense64/ReluRelu3_dense64/BiasAdd:output:0*
T0*'
_output_shapes
:���������@2
3_dense64/Relu�
4_dense32/MatMul/ReadVariableOpReadVariableOp(dense32_matmul_readvariableop_resource_0*
_output_shapes

:@ *
dtype02!
4_dense32/MatMul/ReadVariableOp�
4_dense32/MatMulMatMul3_dense64/Relu:activations:0'4_dense32/MatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:��������� 2
4_dense32/MatMul�
 4_dense32/BiasAdd/ReadVariableOpReadVariableOp)dense32_biasadd_readvariableop_resource_0*
_output_shapes
: *
dtype02"
 4_dense32/BiasAdd/ReadVariableOp�
4_dense32/BiasAddBiasAdd4_dense32/MatMul:product:0(4_dense32/BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:��������� 2
4_dense32/BiasAddv
4_dense32/ReluRelu4_dense32/BiasAdd:output:0*
T0*'
_output_shapes
:��������� 2
4_dense32/Relu�
5_dense18/MatMul/ReadVariableOpReadVariableOp(dense18_matmul_readvariableop_resource_0*
_output_shapes

: *
dtype02!
5_dense18/MatMul/ReadVariableOp�
5_dense18/MatMulMatMul4_dense32/Relu:activations:0'5_dense18/MatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2
5_dense18/MatMul�
 5_dense18/BiasAdd/ReadVariableOpReadVariableOp)dense18_biasadd_readvariableop_resource_0*
_output_shapes
:*
dtype02"
 5_dense18/BiasAdd/ReadVariableOp�
5_dense18/BiasAddBiasAdd5_dense18/MatMul:product:0(5_dense18/BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2
5_dense18/BiasAddv
5_dense18/ReluRelu5_dense18/BiasAdd:output:0*
T0*'
_output_shapes
:���������2
5_dense18/Relu�
6_dense9/MatMul/ReadVariableOpReadVariableOp%dense9_matmul_readvariableop_resource*
_output_shapes

:	*
dtype02 
6_dense9/MatMul/ReadVariableOp�
6_dense9/MatMulMatMul5_dense18/Relu:activations:0&6_dense9/MatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������	2
6_dense9/MatMul�
6_dense9/BiasAdd/ReadVariableOpReadVariableOp&dense9_biasadd_readvariableop_resource*
_output_shapes
:	*
dtype02!
6_dense9/BiasAdd/ReadVariableOp�
6_dense9/BiasAddBiasAdd6_dense9/MatMul:product:0'6_dense9/BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������	2
6_dense9/BiasAdds
6_dense9/ReluRelu6_dense9/BiasAdd:output:0*
T0*'
_output_shapes
:���������	2
6_dense9/Relu�
$output_mem_clf/MatMul/ReadVariableOpReadVariableOp-output_mem_clf_matmul_readvariableop_resource*
_output_shapes

:	*
dtype02&
$output_mem_clf/MatMul/ReadVariableOp�
output_mem_clf/MatMulMatMul6_dense9/Relu:activations:0,output_mem_clf/MatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2
output_mem_clf/MatMul�
%output_mem_clf/BiasAdd/ReadVariableOpReadVariableOp.output_mem_clf_biasadd_readvariableop_resource*
_output_shapes
:*
dtype02'
%output_mem_clf/BiasAdd/ReadVariableOp�
output_mem_clf/BiasAddBiasAddoutput_mem_clf/MatMul:product:0-output_mem_clf/BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2
output_mem_clf/BiasAdd�
output_mem_clf/SoftmaxSoftmaxoutput_mem_clf/BiasAdd:output:0*
T0*'
_output_shapes
:���������2
output_mem_clf/Softmax{
IdentityIdentity output_mem_clf/Softmax:softmax:0^NoOp*
T0*'
_output_shapes
:���������2

Identity�
NoOpNoOp!^1_dense18/BiasAdd/ReadVariableOp ^1_dense18/MatMul/ReadVariableOp!^2_dense32/BiasAdd/ReadVariableOp ^2_dense32/MatMul/ReadVariableOp!^3_dense64/BiasAdd/ReadVariableOp ^3_dense64/MatMul/ReadVariableOp!^4_dense32/BiasAdd/ReadVariableOp ^4_dense32/MatMul/ReadVariableOp!^5_dense18/BiasAdd/ReadVariableOp ^5_dense18/MatMul/ReadVariableOp ^6_dense9/BiasAdd/ReadVariableOp^6_dense9/MatMul/ReadVariableOp&^output_mem_clf/BiasAdd/ReadVariableOp%^output_mem_clf/MatMul/ReadVariableOp*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime*B
_input_shapes1
/:���������	: : : : : : : : : : : : : : 2D
 1_dense18/BiasAdd/ReadVariableOp 1_dense18/BiasAdd/ReadVariableOp2B
1_dense18/MatMul/ReadVariableOp1_dense18/MatMul/ReadVariableOp2D
 2_dense32/BiasAdd/ReadVariableOp 2_dense32/BiasAdd/ReadVariableOp2B
2_dense32/MatMul/ReadVariableOp2_dense32/MatMul/ReadVariableOp2D
 3_dense64/BiasAdd/ReadVariableOp 3_dense64/BiasAdd/ReadVariableOp2B
3_dense64/MatMul/ReadVariableOp3_dense64/MatMul/ReadVariableOp2D
 4_dense32/BiasAdd/ReadVariableOp 4_dense32/BiasAdd/ReadVariableOp2B
4_dense32/MatMul/ReadVariableOp4_dense32/MatMul/ReadVariableOp2D
 5_dense18/BiasAdd/ReadVariableOp 5_dense18/BiasAdd/ReadVariableOp2B
5_dense18/MatMul/ReadVariableOp5_dense18/MatMul/ReadVariableOp2B
6_dense9/BiasAdd/ReadVariableOp6_dense9/BiasAdd/ReadVariableOp2@
6_dense9/MatMul/ReadVariableOp6_dense9/MatMul/ReadVariableOp2N
%output_mem_clf/BiasAdd/ReadVariableOp%output_mem_clf/BiasAdd/ReadVariableOp2L
$output_mem_clf/MatMul/ReadVariableOp$output_mem_clf/MatMul/ReadVariableOp:O K
'
_output_shapes
:���������	
 
_user_specified_nameinputs
�
�
E__inference_1_dense18_layer_call_and_return_conditional_losses_925987

inputs0
matmul_readvariableop_resource:	-
biasadd_readvariableop_resource:
identity��BiasAdd/ReadVariableOp�MatMul/ReadVariableOp�
MatMul/ReadVariableOpReadVariableOpmatmul_readvariableop_resource*
_output_shapes

:	*
dtype02
MatMul/ReadVariableOps
MatMulMatMulinputsMatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2
MatMul�
BiasAdd/ReadVariableOpReadVariableOpbiasadd_readvariableop_resource*
_output_shapes
:*
dtype02
BiasAdd/ReadVariableOp�
BiasAddBiasAddMatMul:product:0BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2	
BiasAddX
ReluReluBiasAdd:output:0*
T0*'
_output_shapes
:���������2
Relum
IdentityIdentityRelu:activations:0^NoOp*
T0*'
_output_shapes
:���������2

Identity
NoOpNoOp^BiasAdd/ReadVariableOp^MatMul/ReadVariableOp*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime**
_input_shapes
:���������	: : 20
BiasAdd/ReadVariableOpBiasAdd/ReadVariableOp2.
MatMul/ReadVariableOpMatMul/ReadVariableOp:O K
'
_output_shapes
:���������	
 
_user_specified_nameinputs
�(
�
M__inference_memory_classifier_layer_call_and_return_conditional_losses_925724
hst_jobs 
dense18_925688:	
dense18_925690: 
dense32_925693: 
dense32_925695:  
dense64_925698: @
dense64_925700:@ 
dense32_925703:@ 
dense32_925705:  
dense18_925708: 
dense18_925710:
dense9_925713:	
dense9_925715:	'
output_mem_clf_925718:	#
output_mem_clf_925720:
identity��!1_dense18/StatefulPartitionedCall�!2_dense32/StatefulPartitionedCall�!3_dense64/StatefulPartitionedCall�!4_dense32/StatefulPartitionedCall�!5_dense18/StatefulPartitionedCall� 6_dense9/StatefulPartitionedCall�&output_mem_clf/StatefulPartitionedCall�
!1_dense18/StatefulPartitionedCallStatefulPartitionedCallhst_jobsdense18_925688dense18_925690*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������*$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *N
fIRG
E__inference_1_dense18_layer_call_and_return_conditional_losses_9253372#
!1_dense18/StatefulPartitionedCall�
!2_dense32/StatefulPartitionedCallStatefulPartitionedCall*1_dense18/StatefulPartitionedCall:output:0dense32_925693dense32_925695*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:��������� *$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *N
fIRG
E__inference_2_dense32_layer_call_and_return_conditional_losses_9253542#
!2_dense32/StatefulPartitionedCall�
!3_dense64/StatefulPartitionedCallStatefulPartitionedCall*2_dense32/StatefulPartitionedCall:output:0dense64_925698dense64_925700*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������@*$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *N
fIRG
E__inference_3_dense64_layer_call_and_return_conditional_losses_9253712#
!3_dense64/StatefulPartitionedCall�
!4_dense32/StatefulPartitionedCallStatefulPartitionedCall*3_dense64/StatefulPartitionedCall:output:0dense32_925703dense32_925705*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:��������� *$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *N
fIRG
E__inference_4_dense32_layer_call_and_return_conditional_losses_9253882#
!4_dense32/StatefulPartitionedCall�
!5_dense18/StatefulPartitionedCallStatefulPartitionedCall*4_dense32/StatefulPartitionedCall:output:0dense18_925708dense18_925710*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������*$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *N
fIRG
E__inference_5_dense18_layer_call_and_return_conditional_losses_9254052#
!5_dense18/StatefulPartitionedCall�
 6_dense9/StatefulPartitionedCallStatefulPartitionedCall*5_dense18/StatefulPartitionedCall:output:0dense9_925713dense9_925715*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������	*$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *M
fHRF
D__inference_6_dense9_layer_call_and_return_conditional_losses_9254222"
 6_dense9/StatefulPartitionedCall�
&output_mem_clf/StatefulPartitionedCallStatefulPartitionedCall)6_dense9/StatefulPartitionedCall:output:0output_mem_clf_925718output_mem_clf_925720*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������*$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *S
fNRL
J__inference_output_mem_clf_layer_call_and_return_conditional_losses_9254392(
&output_mem_clf/StatefulPartitionedCall�
IdentityIdentity/output_mem_clf/StatefulPartitionedCall:output:0^NoOp*
T0*'
_output_shapes
:���������2

Identity�
NoOpNoOp"^1_dense18/StatefulPartitionedCall"^2_dense32/StatefulPartitionedCall"^3_dense64/StatefulPartitionedCall"^4_dense32/StatefulPartitionedCall"^5_dense18/StatefulPartitionedCall!^6_dense9/StatefulPartitionedCall'^output_mem_clf/StatefulPartitionedCall*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime*B
_input_shapes1
/:���������	: : : : : : : : : : : : : : 2F
!1_dense18/StatefulPartitionedCall!1_dense18/StatefulPartitionedCall2F
!2_dense32/StatefulPartitionedCall!2_dense32/StatefulPartitionedCall2F
!3_dense64/StatefulPartitionedCall!3_dense64/StatefulPartitionedCall2F
!4_dense32/StatefulPartitionedCall!4_dense32/StatefulPartitionedCall2F
!5_dense18/StatefulPartitionedCall!5_dense18/StatefulPartitionedCall2D
 6_dense9/StatefulPartitionedCall 6_dense9/StatefulPartitionedCall2P
&output_mem_clf/StatefulPartitionedCall&output_mem_clf/StatefulPartitionedCall:Q M
'
_output_shapes
:���������	
"
_user_specified_name
hst_jobs
�
�
/__inference_output_mem_clf_layer_call_fn_926116

inputs
unknown:	
	unknown_0:
identity��StatefulPartitionedCall�
StatefulPartitionedCallStatefulPartitionedCallinputsunknown	unknown_0*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������*$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *S
fNRL
J__inference_output_mem_clf_layer_call_and_return_conditional_losses_9254392
StatefulPartitionedCall{
IdentityIdentity StatefulPartitionedCall:output:0^NoOp*
T0*'
_output_shapes
:���������2

Identityh
NoOpNoOp^StatefulPartitionedCall*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime**
_input_shapes
:���������	: : 22
StatefulPartitionedCallStatefulPartitionedCall:O K
'
_output_shapes
:���������	
 
_user_specified_nameinputs
�
�
2__inference_memory_classifier_layer_call_fn_925976

inputs
unknown:	
	unknown_0:
	unknown_1: 
	unknown_2: 
	unknown_3: @
	unknown_4:@
	unknown_5:@ 
	unknown_6: 
	unknown_7: 
	unknown_8:
	unknown_9:	

unknown_10:	

unknown_11:	

unknown_12:
identity��StatefulPartitionedCall�
StatefulPartitionedCallStatefulPartitionedCallinputsunknown	unknown_0	unknown_1	unknown_2	unknown_3	unknown_4	unknown_5	unknown_6	unknown_7	unknown_8	unknown_9
unknown_10
unknown_11
unknown_12*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������*0
_read_only_resource_inputs
	
*-
config_proto

CPU

GPU 2J 8� *V
fQRO
M__inference_memory_classifier_layer_call_and_return_conditional_losses_9256212
StatefulPartitionedCall{
IdentityIdentity StatefulPartitionedCall:output:0^NoOp*
T0*'
_output_shapes
:���������2

Identityh
NoOpNoOp^StatefulPartitionedCall*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime*B
_input_shapes1
/:���������	: : : : : : : : : : : : : : 22
StatefulPartitionedCallStatefulPartitionedCall:O K
'
_output_shapes
:���������	
 
_user_specified_nameinputs
�
�
D__inference_6_dense9_layer_call_and_return_conditional_losses_926087

inputs0
matmul_readvariableop_resource:	-
biasadd_readvariableop_resource:	
identity��BiasAdd/ReadVariableOp�MatMul/ReadVariableOp�
MatMul/ReadVariableOpReadVariableOpmatmul_readvariableop_resource*
_output_shapes

:	*
dtype02
MatMul/ReadVariableOps
MatMulMatMulinputsMatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������	2
MatMul�
BiasAdd/ReadVariableOpReadVariableOpbiasadd_readvariableop_resource*
_output_shapes
:	*
dtype02
BiasAdd/ReadVariableOp�
BiasAddBiasAddMatMul:product:0BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������	2	
BiasAddX
ReluReluBiasAdd:output:0*
T0*'
_output_shapes
:���������	2
Relum
IdentityIdentityRelu:activations:0^NoOp*
T0*'
_output_shapes
:���������	2

Identity
NoOpNoOp^BiasAdd/ReadVariableOp^MatMul/ReadVariableOp*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime**
_input_shapes
:���������: : 20
BiasAdd/ReadVariableOpBiasAdd/ReadVariableOp2.
MatMul/ReadVariableOpMatMul/ReadVariableOp:O K
'
_output_shapes
:���������
 
_user_specified_nameinputs
��
�
"__inference__traced_restore_926455
file_prefix3
!assignvariableop_1_dense18_kernel:	/
!assignvariableop_1_1_dense18_bias:5
#assignvariableop_2_2_dense32_kernel: /
!assignvariableop_3_2_dense32_bias: 5
#assignvariableop_4_3_dense64_kernel: @/
!assignvariableop_5_3_dense64_bias:@5
#assignvariableop_6_4_dense32_kernel:@ /
!assignvariableop_7_4_dense32_bias: 5
#assignvariableop_8_5_dense18_kernel: /
!assignvariableop_9_5_dense18_bias:5
#assignvariableop_10_6_dense9_kernel:	/
!assignvariableop_11_6_dense9_bias:	;
)assignvariableop_12_output_mem_clf_kernel:	5
'assignvariableop_13_output_mem_clf_bias:'
assignvariableop_14_adam_iter:	 )
assignvariableop_15_adam_beta_1: )
assignvariableop_16_adam_beta_2: (
assignvariableop_17_adam_decay: 0
&assignvariableop_18_adam_learning_rate: #
assignvariableop_19_total: #
assignvariableop_20_count: %
assignvariableop_21_total_1: %
assignvariableop_22_count_1: =
+assignvariableop_23_adam_1_dense18_kernel_m:	7
)assignvariableop_24_adam_1_dense18_bias_m:=
+assignvariableop_25_adam_2_dense32_kernel_m: 7
)assignvariableop_26_adam_2_dense32_bias_m: =
+assignvariableop_27_adam_3_dense64_kernel_m: @7
)assignvariableop_28_adam_3_dense64_bias_m:@=
+assignvariableop_29_adam_4_dense32_kernel_m:@ 7
)assignvariableop_30_adam_4_dense32_bias_m: =
+assignvariableop_31_adam_5_dense18_kernel_m: 7
)assignvariableop_32_adam_5_dense18_bias_m:<
*assignvariableop_33_adam_6_dense9_kernel_m:	6
(assignvariableop_34_adam_6_dense9_bias_m:	B
0assignvariableop_35_adam_output_mem_clf_kernel_m:	<
.assignvariableop_36_adam_output_mem_clf_bias_m:=
+assignvariableop_37_adam_1_dense18_kernel_v:	7
)assignvariableop_38_adam_1_dense18_bias_v:=
+assignvariableop_39_adam_2_dense32_kernel_v: 7
)assignvariableop_40_adam_2_dense32_bias_v: =
+assignvariableop_41_adam_3_dense64_kernel_v: @7
)assignvariableop_42_adam_3_dense64_bias_v:@=
+assignvariableop_43_adam_4_dense32_kernel_v:@ 7
)assignvariableop_44_adam_4_dense32_bias_v: =
+assignvariableop_45_adam_5_dense18_kernel_v: 7
)assignvariableop_46_adam_5_dense18_bias_v:<
*assignvariableop_47_adam_6_dense9_kernel_v:	6
(assignvariableop_48_adam_6_dense9_bias_v:	B
0assignvariableop_49_adam_output_mem_clf_kernel_v:	<
.assignvariableop_50_adam_output_mem_clf_bias_v:
identity_52��AssignVariableOp�AssignVariableOp_1�AssignVariableOp_10�AssignVariableOp_11�AssignVariableOp_12�AssignVariableOp_13�AssignVariableOp_14�AssignVariableOp_15�AssignVariableOp_16�AssignVariableOp_17�AssignVariableOp_18�AssignVariableOp_19�AssignVariableOp_2�AssignVariableOp_20�AssignVariableOp_21�AssignVariableOp_22�AssignVariableOp_23�AssignVariableOp_24�AssignVariableOp_25�AssignVariableOp_26�AssignVariableOp_27�AssignVariableOp_28�AssignVariableOp_29�AssignVariableOp_3�AssignVariableOp_30�AssignVariableOp_31�AssignVariableOp_32�AssignVariableOp_33�AssignVariableOp_34�AssignVariableOp_35�AssignVariableOp_36�AssignVariableOp_37�AssignVariableOp_38�AssignVariableOp_39�AssignVariableOp_4�AssignVariableOp_40�AssignVariableOp_41�AssignVariableOp_42�AssignVariableOp_43�AssignVariableOp_44�AssignVariableOp_45�AssignVariableOp_46�AssignVariableOp_47�AssignVariableOp_48�AssignVariableOp_49�AssignVariableOp_5�AssignVariableOp_50�AssignVariableOp_6�AssignVariableOp_7�AssignVariableOp_8�AssignVariableOp_9�
RestoreV2/tensor_namesConst"/device:CPU:0*
_output_shapes
:4*
dtype0*�
value�B�4B6layer_with_weights-0/kernel/.ATTRIBUTES/VARIABLE_VALUEB4layer_with_weights-0/bias/.ATTRIBUTES/VARIABLE_VALUEB6layer_with_weights-1/kernel/.ATTRIBUTES/VARIABLE_VALUEB4layer_with_weights-1/bias/.ATTRIBUTES/VARIABLE_VALUEB6layer_with_weights-2/kernel/.ATTRIBUTES/VARIABLE_VALUEB4layer_with_weights-2/bias/.ATTRIBUTES/VARIABLE_VALUEB6layer_with_weights-3/kernel/.ATTRIBUTES/VARIABLE_VALUEB4layer_with_weights-3/bias/.ATTRIBUTES/VARIABLE_VALUEB6layer_with_weights-4/kernel/.ATTRIBUTES/VARIABLE_VALUEB4layer_with_weights-4/bias/.ATTRIBUTES/VARIABLE_VALUEB6layer_with_weights-5/kernel/.ATTRIBUTES/VARIABLE_VALUEB4layer_with_weights-5/bias/.ATTRIBUTES/VARIABLE_VALUEB6layer_with_weights-6/kernel/.ATTRIBUTES/VARIABLE_VALUEB4layer_with_weights-6/bias/.ATTRIBUTES/VARIABLE_VALUEB)optimizer/iter/.ATTRIBUTES/VARIABLE_VALUEB+optimizer/beta_1/.ATTRIBUTES/VARIABLE_VALUEB+optimizer/beta_2/.ATTRIBUTES/VARIABLE_VALUEB*optimizer/decay/.ATTRIBUTES/VARIABLE_VALUEB2optimizer/learning_rate/.ATTRIBUTES/VARIABLE_VALUEB4keras_api/metrics/0/total/.ATTRIBUTES/VARIABLE_VALUEB4keras_api/metrics/0/count/.ATTRIBUTES/VARIABLE_VALUEB4keras_api/metrics/1/total/.ATTRIBUTES/VARIABLE_VALUEB4keras_api/metrics/1/count/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-0/kernel/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-0/bias/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-1/kernel/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-1/bias/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-2/kernel/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-2/bias/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-3/kernel/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-3/bias/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-4/kernel/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-4/bias/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-5/kernel/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-5/bias/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-6/kernel/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-6/bias/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-0/kernel/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-0/bias/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-1/kernel/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-1/bias/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-2/kernel/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-2/bias/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-3/kernel/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-3/bias/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-4/kernel/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-4/bias/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-5/kernel/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-5/bias/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-6/kernel/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-6/bias/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEB_CHECKPOINTABLE_OBJECT_GRAPH2
RestoreV2/tensor_names�
RestoreV2/shape_and_slicesConst"/device:CPU:0*
_output_shapes
:4*
dtype0*{
valuerBp4B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B 2
RestoreV2/shape_and_slices�
	RestoreV2	RestoreV2file_prefixRestoreV2/tensor_names:output:0#RestoreV2/shape_and_slices:output:0"/device:CPU:0*�
_output_shapes�
�::::::::::::::::::::::::::::::::::::::::::::::::::::*B
dtypes8
624	2
	RestoreV2g
IdentityIdentityRestoreV2:tensors:0"/device:CPU:0*
T0*
_output_shapes
:2

Identity�
AssignVariableOpAssignVariableOp!assignvariableop_1_dense18_kernelIdentity:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOpk

Identity_1IdentityRestoreV2:tensors:1"/device:CPU:0*
T0*
_output_shapes
:2

Identity_1�
AssignVariableOp_1AssignVariableOp!assignvariableop_1_1_dense18_biasIdentity_1:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_1k

Identity_2IdentityRestoreV2:tensors:2"/device:CPU:0*
T0*
_output_shapes
:2

Identity_2�
AssignVariableOp_2AssignVariableOp#assignvariableop_2_2_dense32_kernelIdentity_2:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_2k

Identity_3IdentityRestoreV2:tensors:3"/device:CPU:0*
T0*
_output_shapes
:2

Identity_3�
AssignVariableOp_3AssignVariableOp!assignvariableop_3_2_dense32_biasIdentity_3:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_3k

Identity_4IdentityRestoreV2:tensors:4"/device:CPU:0*
T0*
_output_shapes
:2

Identity_4�
AssignVariableOp_4AssignVariableOp#assignvariableop_4_3_dense64_kernelIdentity_4:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_4k

Identity_5IdentityRestoreV2:tensors:5"/device:CPU:0*
T0*
_output_shapes
:2

Identity_5�
AssignVariableOp_5AssignVariableOp!assignvariableop_5_3_dense64_biasIdentity_5:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_5k

Identity_6IdentityRestoreV2:tensors:6"/device:CPU:0*
T0*
_output_shapes
:2

Identity_6�
AssignVariableOp_6AssignVariableOp#assignvariableop_6_4_dense32_kernelIdentity_6:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_6k

Identity_7IdentityRestoreV2:tensors:7"/device:CPU:0*
T0*
_output_shapes
:2

Identity_7�
AssignVariableOp_7AssignVariableOp!assignvariableop_7_4_dense32_biasIdentity_7:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_7k

Identity_8IdentityRestoreV2:tensors:8"/device:CPU:0*
T0*
_output_shapes
:2

Identity_8�
AssignVariableOp_8AssignVariableOp#assignvariableop_8_5_dense18_kernelIdentity_8:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_8k

Identity_9IdentityRestoreV2:tensors:9"/device:CPU:0*
T0*
_output_shapes
:2

Identity_9�
AssignVariableOp_9AssignVariableOp!assignvariableop_9_5_dense18_biasIdentity_9:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_9n
Identity_10IdentityRestoreV2:tensors:10"/device:CPU:0*
T0*
_output_shapes
:2
Identity_10�
AssignVariableOp_10AssignVariableOp#assignvariableop_10_6_dense9_kernelIdentity_10:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_10n
Identity_11IdentityRestoreV2:tensors:11"/device:CPU:0*
T0*
_output_shapes
:2
Identity_11�
AssignVariableOp_11AssignVariableOp!assignvariableop_11_6_dense9_biasIdentity_11:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_11n
Identity_12IdentityRestoreV2:tensors:12"/device:CPU:0*
T0*
_output_shapes
:2
Identity_12�
AssignVariableOp_12AssignVariableOp)assignvariableop_12_output_mem_clf_kernelIdentity_12:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_12n
Identity_13IdentityRestoreV2:tensors:13"/device:CPU:0*
T0*
_output_shapes
:2
Identity_13�
AssignVariableOp_13AssignVariableOp'assignvariableop_13_output_mem_clf_biasIdentity_13:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_13n
Identity_14IdentityRestoreV2:tensors:14"/device:CPU:0*
T0	*
_output_shapes
:2
Identity_14�
AssignVariableOp_14AssignVariableOpassignvariableop_14_adam_iterIdentity_14:output:0"/device:CPU:0*
_output_shapes
 *
dtype0	2
AssignVariableOp_14n
Identity_15IdentityRestoreV2:tensors:15"/device:CPU:0*
T0*
_output_shapes
:2
Identity_15�
AssignVariableOp_15AssignVariableOpassignvariableop_15_adam_beta_1Identity_15:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_15n
Identity_16IdentityRestoreV2:tensors:16"/device:CPU:0*
T0*
_output_shapes
:2
Identity_16�
AssignVariableOp_16AssignVariableOpassignvariableop_16_adam_beta_2Identity_16:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_16n
Identity_17IdentityRestoreV2:tensors:17"/device:CPU:0*
T0*
_output_shapes
:2
Identity_17�
AssignVariableOp_17AssignVariableOpassignvariableop_17_adam_decayIdentity_17:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_17n
Identity_18IdentityRestoreV2:tensors:18"/device:CPU:0*
T0*
_output_shapes
:2
Identity_18�
AssignVariableOp_18AssignVariableOp&assignvariableop_18_adam_learning_rateIdentity_18:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_18n
Identity_19IdentityRestoreV2:tensors:19"/device:CPU:0*
T0*
_output_shapes
:2
Identity_19�
AssignVariableOp_19AssignVariableOpassignvariableop_19_totalIdentity_19:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_19n
Identity_20IdentityRestoreV2:tensors:20"/device:CPU:0*
T0*
_output_shapes
:2
Identity_20�
AssignVariableOp_20AssignVariableOpassignvariableop_20_countIdentity_20:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_20n
Identity_21IdentityRestoreV2:tensors:21"/device:CPU:0*
T0*
_output_shapes
:2
Identity_21�
AssignVariableOp_21AssignVariableOpassignvariableop_21_total_1Identity_21:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_21n
Identity_22IdentityRestoreV2:tensors:22"/device:CPU:0*
T0*
_output_shapes
:2
Identity_22�
AssignVariableOp_22AssignVariableOpassignvariableop_22_count_1Identity_22:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_22n
Identity_23IdentityRestoreV2:tensors:23"/device:CPU:0*
T0*
_output_shapes
:2
Identity_23�
AssignVariableOp_23AssignVariableOp+assignvariableop_23_adam_1_dense18_kernel_mIdentity_23:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_23n
Identity_24IdentityRestoreV2:tensors:24"/device:CPU:0*
T0*
_output_shapes
:2
Identity_24�
AssignVariableOp_24AssignVariableOp)assignvariableop_24_adam_1_dense18_bias_mIdentity_24:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_24n
Identity_25IdentityRestoreV2:tensors:25"/device:CPU:0*
T0*
_output_shapes
:2
Identity_25�
AssignVariableOp_25AssignVariableOp+assignvariableop_25_adam_2_dense32_kernel_mIdentity_25:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_25n
Identity_26IdentityRestoreV2:tensors:26"/device:CPU:0*
T0*
_output_shapes
:2
Identity_26�
AssignVariableOp_26AssignVariableOp)assignvariableop_26_adam_2_dense32_bias_mIdentity_26:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_26n
Identity_27IdentityRestoreV2:tensors:27"/device:CPU:0*
T0*
_output_shapes
:2
Identity_27�
AssignVariableOp_27AssignVariableOp+assignvariableop_27_adam_3_dense64_kernel_mIdentity_27:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_27n
Identity_28IdentityRestoreV2:tensors:28"/device:CPU:0*
T0*
_output_shapes
:2
Identity_28�
AssignVariableOp_28AssignVariableOp)assignvariableop_28_adam_3_dense64_bias_mIdentity_28:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_28n
Identity_29IdentityRestoreV2:tensors:29"/device:CPU:0*
T0*
_output_shapes
:2
Identity_29�
AssignVariableOp_29AssignVariableOp+assignvariableop_29_adam_4_dense32_kernel_mIdentity_29:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_29n
Identity_30IdentityRestoreV2:tensors:30"/device:CPU:0*
T0*
_output_shapes
:2
Identity_30�
AssignVariableOp_30AssignVariableOp)assignvariableop_30_adam_4_dense32_bias_mIdentity_30:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_30n
Identity_31IdentityRestoreV2:tensors:31"/device:CPU:0*
T0*
_output_shapes
:2
Identity_31�
AssignVariableOp_31AssignVariableOp+assignvariableop_31_adam_5_dense18_kernel_mIdentity_31:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_31n
Identity_32IdentityRestoreV2:tensors:32"/device:CPU:0*
T0*
_output_shapes
:2
Identity_32�
AssignVariableOp_32AssignVariableOp)assignvariableop_32_adam_5_dense18_bias_mIdentity_32:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_32n
Identity_33IdentityRestoreV2:tensors:33"/device:CPU:0*
T0*
_output_shapes
:2
Identity_33�
AssignVariableOp_33AssignVariableOp*assignvariableop_33_adam_6_dense9_kernel_mIdentity_33:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_33n
Identity_34IdentityRestoreV2:tensors:34"/device:CPU:0*
T0*
_output_shapes
:2
Identity_34�
AssignVariableOp_34AssignVariableOp(assignvariableop_34_adam_6_dense9_bias_mIdentity_34:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_34n
Identity_35IdentityRestoreV2:tensors:35"/device:CPU:0*
T0*
_output_shapes
:2
Identity_35�
AssignVariableOp_35AssignVariableOp0assignvariableop_35_adam_output_mem_clf_kernel_mIdentity_35:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_35n
Identity_36IdentityRestoreV2:tensors:36"/device:CPU:0*
T0*
_output_shapes
:2
Identity_36�
AssignVariableOp_36AssignVariableOp.assignvariableop_36_adam_output_mem_clf_bias_mIdentity_36:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_36n
Identity_37IdentityRestoreV2:tensors:37"/device:CPU:0*
T0*
_output_shapes
:2
Identity_37�
AssignVariableOp_37AssignVariableOp+assignvariableop_37_adam_1_dense18_kernel_vIdentity_37:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_37n
Identity_38IdentityRestoreV2:tensors:38"/device:CPU:0*
T0*
_output_shapes
:2
Identity_38�
AssignVariableOp_38AssignVariableOp)assignvariableop_38_adam_1_dense18_bias_vIdentity_38:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_38n
Identity_39IdentityRestoreV2:tensors:39"/device:CPU:0*
T0*
_output_shapes
:2
Identity_39�
AssignVariableOp_39AssignVariableOp+assignvariableop_39_adam_2_dense32_kernel_vIdentity_39:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_39n
Identity_40IdentityRestoreV2:tensors:40"/device:CPU:0*
T0*
_output_shapes
:2
Identity_40�
AssignVariableOp_40AssignVariableOp)assignvariableop_40_adam_2_dense32_bias_vIdentity_40:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_40n
Identity_41IdentityRestoreV2:tensors:41"/device:CPU:0*
T0*
_output_shapes
:2
Identity_41�
AssignVariableOp_41AssignVariableOp+assignvariableop_41_adam_3_dense64_kernel_vIdentity_41:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_41n
Identity_42IdentityRestoreV2:tensors:42"/device:CPU:0*
T0*
_output_shapes
:2
Identity_42�
AssignVariableOp_42AssignVariableOp)assignvariableop_42_adam_3_dense64_bias_vIdentity_42:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_42n
Identity_43IdentityRestoreV2:tensors:43"/device:CPU:0*
T0*
_output_shapes
:2
Identity_43�
AssignVariableOp_43AssignVariableOp+assignvariableop_43_adam_4_dense32_kernel_vIdentity_43:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_43n
Identity_44IdentityRestoreV2:tensors:44"/device:CPU:0*
T0*
_output_shapes
:2
Identity_44�
AssignVariableOp_44AssignVariableOp)assignvariableop_44_adam_4_dense32_bias_vIdentity_44:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_44n
Identity_45IdentityRestoreV2:tensors:45"/device:CPU:0*
T0*
_output_shapes
:2
Identity_45�
AssignVariableOp_45AssignVariableOp+assignvariableop_45_adam_5_dense18_kernel_vIdentity_45:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_45n
Identity_46IdentityRestoreV2:tensors:46"/device:CPU:0*
T0*
_output_shapes
:2
Identity_46�
AssignVariableOp_46AssignVariableOp)assignvariableop_46_adam_5_dense18_bias_vIdentity_46:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_46n
Identity_47IdentityRestoreV2:tensors:47"/device:CPU:0*
T0*
_output_shapes
:2
Identity_47�
AssignVariableOp_47AssignVariableOp*assignvariableop_47_adam_6_dense9_kernel_vIdentity_47:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_47n
Identity_48IdentityRestoreV2:tensors:48"/device:CPU:0*
T0*
_output_shapes
:2
Identity_48�
AssignVariableOp_48AssignVariableOp(assignvariableop_48_adam_6_dense9_bias_vIdentity_48:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_48n
Identity_49IdentityRestoreV2:tensors:49"/device:CPU:0*
T0*
_output_shapes
:2
Identity_49�
AssignVariableOp_49AssignVariableOp0assignvariableop_49_adam_output_mem_clf_kernel_vIdentity_49:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_49n
Identity_50IdentityRestoreV2:tensors:50"/device:CPU:0*
T0*
_output_shapes
:2
Identity_50�
AssignVariableOp_50AssignVariableOp.assignvariableop_50_adam_output_mem_clf_bias_vIdentity_50:output:0"/device:CPU:0*
_output_shapes
 *
dtype02
AssignVariableOp_509
NoOpNoOp"/device:CPU:0*
_output_shapes
 2
NoOp�	
Identity_51Identityfile_prefix^AssignVariableOp^AssignVariableOp_1^AssignVariableOp_10^AssignVariableOp_11^AssignVariableOp_12^AssignVariableOp_13^AssignVariableOp_14^AssignVariableOp_15^AssignVariableOp_16^AssignVariableOp_17^AssignVariableOp_18^AssignVariableOp_19^AssignVariableOp_2^AssignVariableOp_20^AssignVariableOp_21^AssignVariableOp_22^AssignVariableOp_23^AssignVariableOp_24^AssignVariableOp_25^AssignVariableOp_26^AssignVariableOp_27^AssignVariableOp_28^AssignVariableOp_29^AssignVariableOp_3^AssignVariableOp_30^AssignVariableOp_31^AssignVariableOp_32^AssignVariableOp_33^AssignVariableOp_34^AssignVariableOp_35^AssignVariableOp_36^AssignVariableOp_37^AssignVariableOp_38^AssignVariableOp_39^AssignVariableOp_4^AssignVariableOp_40^AssignVariableOp_41^AssignVariableOp_42^AssignVariableOp_43^AssignVariableOp_44^AssignVariableOp_45^AssignVariableOp_46^AssignVariableOp_47^AssignVariableOp_48^AssignVariableOp_49^AssignVariableOp_5^AssignVariableOp_50^AssignVariableOp_6^AssignVariableOp_7^AssignVariableOp_8^AssignVariableOp_9^NoOp"/device:CPU:0*
T0*
_output_shapes
: 2
Identity_51f
Identity_52IdentityIdentity_51:output:0^NoOp_1*
T0*
_output_shapes
: 2
Identity_52�	
NoOp_1NoOp^AssignVariableOp^AssignVariableOp_1^AssignVariableOp_10^AssignVariableOp_11^AssignVariableOp_12^AssignVariableOp_13^AssignVariableOp_14^AssignVariableOp_15^AssignVariableOp_16^AssignVariableOp_17^AssignVariableOp_18^AssignVariableOp_19^AssignVariableOp_2^AssignVariableOp_20^AssignVariableOp_21^AssignVariableOp_22^AssignVariableOp_23^AssignVariableOp_24^AssignVariableOp_25^AssignVariableOp_26^AssignVariableOp_27^AssignVariableOp_28^AssignVariableOp_29^AssignVariableOp_3^AssignVariableOp_30^AssignVariableOp_31^AssignVariableOp_32^AssignVariableOp_33^AssignVariableOp_34^AssignVariableOp_35^AssignVariableOp_36^AssignVariableOp_37^AssignVariableOp_38^AssignVariableOp_39^AssignVariableOp_4^AssignVariableOp_40^AssignVariableOp_41^AssignVariableOp_42^AssignVariableOp_43^AssignVariableOp_44^AssignVariableOp_45^AssignVariableOp_46^AssignVariableOp_47^AssignVariableOp_48^AssignVariableOp_49^AssignVariableOp_5^AssignVariableOp_50^AssignVariableOp_6^AssignVariableOp_7^AssignVariableOp_8^AssignVariableOp_9*"
_acd_function_control_output(*
_output_shapes
 2
NoOp_1"#
identity_52Identity_52:output:0*{
_input_shapesj
h: : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : 2$
AssignVariableOpAssignVariableOp2(
AssignVariableOp_1AssignVariableOp_12*
AssignVariableOp_10AssignVariableOp_102*
AssignVariableOp_11AssignVariableOp_112*
AssignVariableOp_12AssignVariableOp_122*
AssignVariableOp_13AssignVariableOp_132*
AssignVariableOp_14AssignVariableOp_142*
AssignVariableOp_15AssignVariableOp_152*
AssignVariableOp_16AssignVariableOp_162*
AssignVariableOp_17AssignVariableOp_172*
AssignVariableOp_18AssignVariableOp_182*
AssignVariableOp_19AssignVariableOp_192(
AssignVariableOp_2AssignVariableOp_22*
AssignVariableOp_20AssignVariableOp_202*
AssignVariableOp_21AssignVariableOp_212*
AssignVariableOp_22AssignVariableOp_222*
AssignVariableOp_23AssignVariableOp_232*
AssignVariableOp_24AssignVariableOp_242*
AssignVariableOp_25AssignVariableOp_252*
AssignVariableOp_26AssignVariableOp_262*
AssignVariableOp_27AssignVariableOp_272*
AssignVariableOp_28AssignVariableOp_282*
AssignVariableOp_29AssignVariableOp_292(
AssignVariableOp_3AssignVariableOp_32*
AssignVariableOp_30AssignVariableOp_302*
AssignVariableOp_31AssignVariableOp_312*
AssignVariableOp_32AssignVariableOp_322*
AssignVariableOp_33AssignVariableOp_332*
AssignVariableOp_34AssignVariableOp_342*
AssignVariableOp_35AssignVariableOp_352*
AssignVariableOp_36AssignVariableOp_362*
AssignVariableOp_37AssignVariableOp_372*
AssignVariableOp_38AssignVariableOp_382*
AssignVariableOp_39AssignVariableOp_392(
AssignVariableOp_4AssignVariableOp_42*
AssignVariableOp_40AssignVariableOp_402*
AssignVariableOp_41AssignVariableOp_412*
AssignVariableOp_42AssignVariableOp_422*
AssignVariableOp_43AssignVariableOp_432*
AssignVariableOp_44AssignVariableOp_442*
AssignVariableOp_45AssignVariableOp_452*
AssignVariableOp_46AssignVariableOp_462*
AssignVariableOp_47AssignVariableOp_472*
AssignVariableOp_48AssignVariableOp_482*
AssignVariableOp_49AssignVariableOp_492(
AssignVariableOp_5AssignVariableOp_52*
AssignVariableOp_50AssignVariableOp_502(
AssignVariableOp_6AssignVariableOp_62(
AssignVariableOp_7AssignVariableOp_72(
AssignVariableOp_8AssignVariableOp_82(
AssignVariableOp_9AssignVariableOp_9:C ?

_output_shapes
: 
%
_user_specified_namefile_prefix
�
�
E__inference_1_dense18_layer_call_and_return_conditional_losses_925337

inputs0
matmul_readvariableop_resource:	-
biasadd_readvariableop_resource:
identity��BiasAdd/ReadVariableOp�MatMul/ReadVariableOp�
MatMul/ReadVariableOpReadVariableOpmatmul_readvariableop_resource*
_output_shapes

:	*
dtype02
MatMul/ReadVariableOps
MatMulMatMulinputsMatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2
MatMul�
BiasAdd/ReadVariableOpReadVariableOpbiasadd_readvariableop_resource*
_output_shapes
:*
dtype02
BiasAdd/ReadVariableOp�
BiasAddBiasAddMatMul:product:0BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2	
BiasAddX
ReluReluBiasAdd:output:0*
T0*'
_output_shapes
:���������2
Relum
IdentityIdentityRelu:activations:0^NoOp*
T0*'
_output_shapes
:���������2

Identity
NoOpNoOp^BiasAdd/ReadVariableOp^MatMul/ReadVariableOp*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime**
_input_shapes
:���������	: : 20
BiasAdd/ReadVariableOpBiasAdd/ReadVariableOp2.
MatMul/ReadVariableOpMatMul/ReadVariableOp:O K
'
_output_shapes
:���������	
 
_user_specified_nameinputs
�
�
J__inference_output_mem_clf_layer_call_and_return_conditional_losses_925439

inputs0
matmul_readvariableop_resource:	-
biasadd_readvariableop_resource:
identity��BiasAdd/ReadVariableOp�MatMul/ReadVariableOp�
MatMul/ReadVariableOpReadVariableOpmatmul_readvariableop_resource*
_output_shapes

:	*
dtype02
MatMul/ReadVariableOps
MatMulMatMulinputsMatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2
MatMul�
BiasAdd/ReadVariableOpReadVariableOpbiasadd_readvariableop_resource*
_output_shapes
:*
dtype02
BiasAdd/ReadVariableOp�
BiasAddBiasAddMatMul:product:0BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2	
BiasAdda
SoftmaxSoftmaxBiasAdd:output:0*
T0*'
_output_shapes
:���������2	
Softmaxl
IdentityIdentitySoftmax:softmax:0^NoOp*
T0*'
_output_shapes
:���������2

Identity
NoOpNoOp^BiasAdd/ReadVariableOp^MatMul/ReadVariableOp*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime**
_input_shapes
:���������	: : 20
BiasAdd/ReadVariableOpBiasAdd/ReadVariableOp2.
MatMul/ReadVariableOpMatMul/ReadVariableOp:O K
'
_output_shapes
:���������	
 
_user_specified_nameinputs
�
�
*__inference_3_dense64_layer_call_fn_926036

inputs
unknown: @
	unknown_0:@
identity��StatefulPartitionedCall�
StatefulPartitionedCallStatefulPartitionedCallinputsunknown	unknown_0*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������@*$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *N
fIRG
E__inference_3_dense64_layer_call_and_return_conditional_losses_9253712
StatefulPartitionedCall{
IdentityIdentity StatefulPartitionedCall:output:0^NoOp*
T0*'
_output_shapes
:���������@2

Identityh
NoOpNoOp^StatefulPartitionedCall*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime**
_input_shapes
:��������� : : 22
StatefulPartitionedCallStatefulPartitionedCall:O K
'
_output_shapes
:��������� 
 
_user_specified_nameinputs
�
�
*__inference_1_dense18_layer_call_fn_925996

inputs
unknown:	
	unknown_0:
identity��StatefulPartitionedCall�
StatefulPartitionedCallStatefulPartitionedCallinputsunknown	unknown_0*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������*$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *N
fIRG
E__inference_1_dense18_layer_call_and_return_conditional_losses_9253372
StatefulPartitionedCall{
IdentityIdentity StatefulPartitionedCall:output:0^NoOp*
T0*'
_output_shapes
:���������2

Identityh
NoOpNoOp^StatefulPartitionedCall*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime**
_input_shapes
:���������	: : 22
StatefulPartitionedCallStatefulPartitionedCall:O K
'
_output_shapes
:���������	
 
_user_specified_nameinputs
�
�
2__inference_memory_classifier_layer_call_fn_925685
hst_jobs
unknown:	
	unknown_0:
	unknown_1: 
	unknown_2: 
	unknown_3: @
	unknown_4:@
	unknown_5:@ 
	unknown_6: 
	unknown_7: 
	unknown_8:
	unknown_9:	

unknown_10:	

unknown_11:	

unknown_12:
identity��StatefulPartitionedCall�
StatefulPartitionedCallStatefulPartitionedCallhst_jobsunknown	unknown_0	unknown_1	unknown_2	unknown_3	unknown_4	unknown_5	unknown_6	unknown_7	unknown_8	unknown_9
unknown_10
unknown_11
unknown_12*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������*0
_read_only_resource_inputs
	
*-
config_proto

CPU

GPU 2J 8� *V
fQRO
M__inference_memory_classifier_layer_call_and_return_conditional_losses_9256212
StatefulPartitionedCall{
IdentityIdentity StatefulPartitionedCall:output:0^NoOp*
T0*'
_output_shapes
:���������2

Identityh
NoOpNoOp^StatefulPartitionedCall*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime*B
_input_shapes1
/:���������	: : : : : : : : : : : : : : 22
StatefulPartitionedCallStatefulPartitionedCall:Q M
'
_output_shapes
:���������	
"
_user_specified_name
hst_jobs
�
�
2__inference_memory_classifier_layer_call_fn_925477
hst_jobs
unknown:	
	unknown_0:
	unknown_1: 
	unknown_2: 
	unknown_3: @
	unknown_4:@
	unknown_5:@ 
	unknown_6: 
	unknown_7: 
	unknown_8:
	unknown_9:	

unknown_10:	

unknown_11:	

unknown_12:
identity��StatefulPartitionedCall�
StatefulPartitionedCallStatefulPartitionedCallhst_jobsunknown	unknown_0	unknown_1	unknown_2	unknown_3	unknown_4	unknown_5	unknown_6	unknown_7	unknown_8	unknown_9
unknown_10
unknown_11
unknown_12*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������*0
_read_only_resource_inputs
	
*-
config_proto

CPU

GPU 2J 8� *V
fQRO
M__inference_memory_classifier_layer_call_and_return_conditional_losses_9254462
StatefulPartitionedCall{
IdentityIdentity StatefulPartitionedCall:output:0^NoOp*
T0*'
_output_shapes
:���������2

Identityh
NoOpNoOp^StatefulPartitionedCall*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime*B
_input_shapes1
/:���������	: : : : : : : : : : : : : : 22
StatefulPartitionedCallStatefulPartitionedCall:Q M
'
_output_shapes
:���������	
"
_user_specified_name
hst_jobs
�`
�
!__inference__wrapped_model_925319
hst_jobsL
:memory_classifier_1_dense18_matmul_readvariableop_resource:	I
;memory_classifier_1_dense18_biasadd_readvariableop_resource:L
:memory_classifier_2_dense32_matmul_readvariableop_resource: I
;memory_classifier_2_dense32_biasadd_readvariableop_resource: L
:memory_classifier_3_dense64_matmul_readvariableop_resource: @I
;memory_classifier_3_dense64_biasadd_readvariableop_resource:@L
:memory_classifier_4_dense32_matmul_readvariableop_resource:@ I
;memory_classifier_4_dense32_biasadd_readvariableop_resource: L
:memory_classifier_5_dense18_matmul_readvariableop_resource: I
;memory_classifier_5_dense18_biasadd_readvariableop_resource:K
9memory_classifier_6_dense9_matmul_readvariableop_resource:	H
:memory_classifier_6_dense9_biasadd_readvariableop_resource:	Q
?memory_classifier_output_mem_clf_matmul_readvariableop_resource:	N
@memory_classifier_output_mem_clf_biasadd_readvariableop_resource:
identity��2memory_classifier/1_dense18/BiasAdd/ReadVariableOp�1memory_classifier/1_dense18/MatMul/ReadVariableOp�2memory_classifier/2_dense32/BiasAdd/ReadVariableOp�1memory_classifier/2_dense32/MatMul/ReadVariableOp�2memory_classifier/3_dense64/BiasAdd/ReadVariableOp�1memory_classifier/3_dense64/MatMul/ReadVariableOp�2memory_classifier/4_dense32/BiasAdd/ReadVariableOp�1memory_classifier/4_dense32/MatMul/ReadVariableOp�2memory_classifier/5_dense18/BiasAdd/ReadVariableOp�1memory_classifier/5_dense18/MatMul/ReadVariableOp�1memory_classifier/6_dense9/BiasAdd/ReadVariableOp�0memory_classifier/6_dense9/MatMul/ReadVariableOp�7memory_classifier/output_mem_clf/BiasAdd/ReadVariableOp�6memory_classifier/output_mem_clf/MatMul/ReadVariableOp�
1memory_classifier/1_dense18/MatMul/ReadVariableOpReadVariableOp:memory_classifier_1_dense18_matmul_readvariableop_resource*
_output_shapes

:	*
dtype023
1memory_classifier/1_dense18/MatMul/ReadVariableOp�
"memory_classifier/1_dense18/MatMulMatMulhst_jobs9memory_classifier/1_dense18/MatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2$
"memory_classifier/1_dense18/MatMul�
2memory_classifier/1_dense18/BiasAdd/ReadVariableOpReadVariableOp;memory_classifier_1_dense18_biasadd_readvariableop_resource*
_output_shapes
:*
dtype024
2memory_classifier/1_dense18/BiasAdd/ReadVariableOp�
#memory_classifier/1_dense18/BiasAddBiasAdd,memory_classifier/1_dense18/MatMul:product:0:memory_classifier/1_dense18/BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2%
#memory_classifier/1_dense18/BiasAdd�
 memory_classifier/1_dense18/ReluRelu,memory_classifier/1_dense18/BiasAdd:output:0*
T0*'
_output_shapes
:���������2"
 memory_classifier/1_dense18/Relu�
1memory_classifier/2_dense32/MatMul/ReadVariableOpReadVariableOp:memory_classifier_2_dense32_matmul_readvariableop_resource*
_output_shapes

: *
dtype023
1memory_classifier/2_dense32/MatMul/ReadVariableOp�
"memory_classifier/2_dense32/MatMulMatMul.memory_classifier/1_dense18/Relu:activations:09memory_classifier/2_dense32/MatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:��������� 2$
"memory_classifier/2_dense32/MatMul�
2memory_classifier/2_dense32/BiasAdd/ReadVariableOpReadVariableOp;memory_classifier_2_dense32_biasadd_readvariableop_resource*
_output_shapes
: *
dtype024
2memory_classifier/2_dense32/BiasAdd/ReadVariableOp�
#memory_classifier/2_dense32/BiasAddBiasAdd,memory_classifier/2_dense32/MatMul:product:0:memory_classifier/2_dense32/BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:��������� 2%
#memory_classifier/2_dense32/BiasAdd�
 memory_classifier/2_dense32/ReluRelu,memory_classifier/2_dense32/BiasAdd:output:0*
T0*'
_output_shapes
:��������� 2"
 memory_classifier/2_dense32/Relu�
1memory_classifier/3_dense64/MatMul/ReadVariableOpReadVariableOp:memory_classifier_3_dense64_matmul_readvariableop_resource*
_output_shapes

: @*
dtype023
1memory_classifier/3_dense64/MatMul/ReadVariableOp�
"memory_classifier/3_dense64/MatMulMatMul.memory_classifier/2_dense32/Relu:activations:09memory_classifier/3_dense64/MatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������@2$
"memory_classifier/3_dense64/MatMul�
2memory_classifier/3_dense64/BiasAdd/ReadVariableOpReadVariableOp;memory_classifier_3_dense64_biasadd_readvariableop_resource*
_output_shapes
:@*
dtype024
2memory_classifier/3_dense64/BiasAdd/ReadVariableOp�
#memory_classifier/3_dense64/BiasAddBiasAdd,memory_classifier/3_dense64/MatMul:product:0:memory_classifier/3_dense64/BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������@2%
#memory_classifier/3_dense64/BiasAdd�
 memory_classifier/3_dense64/ReluRelu,memory_classifier/3_dense64/BiasAdd:output:0*
T0*'
_output_shapes
:���������@2"
 memory_classifier/3_dense64/Relu�
1memory_classifier/4_dense32/MatMul/ReadVariableOpReadVariableOp:memory_classifier_4_dense32_matmul_readvariableop_resource*
_output_shapes

:@ *
dtype023
1memory_classifier/4_dense32/MatMul/ReadVariableOp�
"memory_classifier/4_dense32/MatMulMatMul.memory_classifier/3_dense64/Relu:activations:09memory_classifier/4_dense32/MatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:��������� 2$
"memory_classifier/4_dense32/MatMul�
2memory_classifier/4_dense32/BiasAdd/ReadVariableOpReadVariableOp;memory_classifier_4_dense32_biasadd_readvariableop_resource*
_output_shapes
: *
dtype024
2memory_classifier/4_dense32/BiasAdd/ReadVariableOp�
#memory_classifier/4_dense32/BiasAddBiasAdd,memory_classifier/4_dense32/MatMul:product:0:memory_classifier/4_dense32/BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:��������� 2%
#memory_classifier/4_dense32/BiasAdd�
 memory_classifier/4_dense32/ReluRelu,memory_classifier/4_dense32/BiasAdd:output:0*
T0*'
_output_shapes
:��������� 2"
 memory_classifier/4_dense32/Relu�
1memory_classifier/5_dense18/MatMul/ReadVariableOpReadVariableOp:memory_classifier_5_dense18_matmul_readvariableop_resource*
_output_shapes

: *
dtype023
1memory_classifier/5_dense18/MatMul/ReadVariableOp�
"memory_classifier/5_dense18/MatMulMatMul.memory_classifier/4_dense32/Relu:activations:09memory_classifier/5_dense18/MatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2$
"memory_classifier/5_dense18/MatMul�
2memory_classifier/5_dense18/BiasAdd/ReadVariableOpReadVariableOp;memory_classifier_5_dense18_biasadd_readvariableop_resource*
_output_shapes
:*
dtype024
2memory_classifier/5_dense18/BiasAdd/ReadVariableOp�
#memory_classifier/5_dense18/BiasAddBiasAdd,memory_classifier/5_dense18/MatMul:product:0:memory_classifier/5_dense18/BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2%
#memory_classifier/5_dense18/BiasAdd�
 memory_classifier/5_dense18/ReluRelu,memory_classifier/5_dense18/BiasAdd:output:0*
T0*'
_output_shapes
:���������2"
 memory_classifier/5_dense18/Relu�
0memory_classifier/6_dense9/MatMul/ReadVariableOpReadVariableOp9memory_classifier_6_dense9_matmul_readvariableop_resource*
_output_shapes

:	*
dtype022
0memory_classifier/6_dense9/MatMul/ReadVariableOp�
!memory_classifier/6_dense9/MatMulMatMul.memory_classifier/5_dense18/Relu:activations:08memory_classifier/6_dense9/MatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������	2#
!memory_classifier/6_dense9/MatMul�
1memory_classifier/6_dense9/BiasAdd/ReadVariableOpReadVariableOp:memory_classifier_6_dense9_biasadd_readvariableop_resource*
_output_shapes
:	*
dtype023
1memory_classifier/6_dense9/BiasAdd/ReadVariableOp�
"memory_classifier/6_dense9/BiasAddBiasAdd+memory_classifier/6_dense9/MatMul:product:09memory_classifier/6_dense9/BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������	2$
"memory_classifier/6_dense9/BiasAdd�
memory_classifier/6_dense9/ReluRelu+memory_classifier/6_dense9/BiasAdd:output:0*
T0*'
_output_shapes
:���������	2!
memory_classifier/6_dense9/Relu�
6memory_classifier/output_mem_clf/MatMul/ReadVariableOpReadVariableOp?memory_classifier_output_mem_clf_matmul_readvariableop_resource*
_output_shapes

:	*
dtype028
6memory_classifier/output_mem_clf/MatMul/ReadVariableOp�
'memory_classifier/output_mem_clf/MatMulMatMul-memory_classifier/6_dense9/Relu:activations:0>memory_classifier/output_mem_clf/MatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2)
'memory_classifier/output_mem_clf/MatMul�
7memory_classifier/output_mem_clf/BiasAdd/ReadVariableOpReadVariableOp@memory_classifier_output_mem_clf_biasadd_readvariableop_resource*
_output_shapes
:*
dtype029
7memory_classifier/output_mem_clf/BiasAdd/ReadVariableOp�
(memory_classifier/output_mem_clf/BiasAddBiasAdd1memory_classifier/output_mem_clf/MatMul:product:0?memory_classifier/output_mem_clf/BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2*
(memory_classifier/output_mem_clf/BiasAdd�
(memory_classifier/output_mem_clf/SoftmaxSoftmax1memory_classifier/output_mem_clf/BiasAdd:output:0*
T0*'
_output_shapes
:���������2*
(memory_classifier/output_mem_clf/Softmax�
IdentityIdentity2memory_classifier/output_mem_clf/Softmax:softmax:0^NoOp*
T0*'
_output_shapes
:���������2

Identity�
NoOpNoOp3^memory_classifier/1_dense18/BiasAdd/ReadVariableOp2^memory_classifier/1_dense18/MatMul/ReadVariableOp3^memory_classifier/2_dense32/BiasAdd/ReadVariableOp2^memory_classifier/2_dense32/MatMul/ReadVariableOp3^memory_classifier/3_dense64/BiasAdd/ReadVariableOp2^memory_classifier/3_dense64/MatMul/ReadVariableOp3^memory_classifier/4_dense32/BiasAdd/ReadVariableOp2^memory_classifier/4_dense32/MatMul/ReadVariableOp3^memory_classifier/5_dense18/BiasAdd/ReadVariableOp2^memory_classifier/5_dense18/MatMul/ReadVariableOp2^memory_classifier/6_dense9/BiasAdd/ReadVariableOp1^memory_classifier/6_dense9/MatMul/ReadVariableOp8^memory_classifier/output_mem_clf/BiasAdd/ReadVariableOp7^memory_classifier/output_mem_clf/MatMul/ReadVariableOp*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime*B
_input_shapes1
/:���������	: : : : : : : : : : : : : : 2h
2memory_classifier/1_dense18/BiasAdd/ReadVariableOp2memory_classifier/1_dense18/BiasAdd/ReadVariableOp2f
1memory_classifier/1_dense18/MatMul/ReadVariableOp1memory_classifier/1_dense18/MatMul/ReadVariableOp2h
2memory_classifier/2_dense32/BiasAdd/ReadVariableOp2memory_classifier/2_dense32/BiasAdd/ReadVariableOp2f
1memory_classifier/2_dense32/MatMul/ReadVariableOp1memory_classifier/2_dense32/MatMul/ReadVariableOp2h
2memory_classifier/3_dense64/BiasAdd/ReadVariableOp2memory_classifier/3_dense64/BiasAdd/ReadVariableOp2f
1memory_classifier/3_dense64/MatMul/ReadVariableOp1memory_classifier/3_dense64/MatMul/ReadVariableOp2h
2memory_classifier/4_dense32/BiasAdd/ReadVariableOp2memory_classifier/4_dense32/BiasAdd/ReadVariableOp2f
1memory_classifier/4_dense32/MatMul/ReadVariableOp1memory_classifier/4_dense32/MatMul/ReadVariableOp2h
2memory_classifier/5_dense18/BiasAdd/ReadVariableOp2memory_classifier/5_dense18/BiasAdd/ReadVariableOp2f
1memory_classifier/5_dense18/MatMul/ReadVariableOp1memory_classifier/5_dense18/MatMul/ReadVariableOp2f
1memory_classifier/6_dense9/BiasAdd/ReadVariableOp1memory_classifier/6_dense9/BiasAdd/ReadVariableOp2d
0memory_classifier/6_dense9/MatMul/ReadVariableOp0memory_classifier/6_dense9/MatMul/ReadVariableOp2r
7memory_classifier/output_mem_clf/BiasAdd/ReadVariableOp7memory_classifier/output_mem_clf/BiasAdd/ReadVariableOp2p
6memory_classifier/output_mem_clf/MatMul/ReadVariableOp6memory_classifier/output_mem_clf/MatMul/ReadVariableOp:Q M
'
_output_shapes
:���������	
"
_user_specified_name
hst_jobs
�
�
2__inference_memory_classifier_layer_call_fn_925943

inputs
unknown:	
	unknown_0:
	unknown_1: 
	unknown_2: 
	unknown_3: @
	unknown_4:@
	unknown_5:@ 
	unknown_6: 
	unknown_7: 
	unknown_8:
	unknown_9:	

unknown_10:	

unknown_11:	

unknown_12:
identity��StatefulPartitionedCall�
StatefulPartitionedCallStatefulPartitionedCallinputsunknown	unknown_0	unknown_1	unknown_2	unknown_3	unknown_4	unknown_5	unknown_6	unknown_7	unknown_8	unknown_9
unknown_10
unknown_11
unknown_12*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������*0
_read_only_resource_inputs
	
*-
config_proto

CPU

GPU 2J 8� *V
fQRO
M__inference_memory_classifier_layer_call_and_return_conditional_losses_9254462
StatefulPartitionedCall{
IdentityIdentity StatefulPartitionedCall:output:0^NoOp*
T0*'
_output_shapes
:���������2

Identityh
NoOpNoOp^StatefulPartitionedCall*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime*B
_input_shapes1
/:���������	: : : : : : : : : : : : : : 22
StatefulPartitionedCallStatefulPartitionedCall:O K
'
_output_shapes
:���������	
 
_user_specified_nameinputs
�
�
J__inference_output_mem_clf_layer_call_and_return_conditional_losses_926107

inputs0
matmul_readvariableop_resource:	-
biasadd_readvariableop_resource:
identity��BiasAdd/ReadVariableOp�MatMul/ReadVariableOp�
MatMul/ReadVariableOpReadVariableOpmatmul_readvariableop_resource*
_output_shapes

:	*
dtype02
MatMul/ReadVariableOps
MatMulMatMulinputsMatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2
MatMul�
BiasAdd/ReadVariableOpReadVariableOpbiasadd_readvariableop_resource*
_output_shapes
:*
dtype02
BiasAdd/ReadVariableOp�
BiasAddBiasAddMatMul:product:0BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2	
BiasAdda
SoftmaxSoftmaxBiasAdd:output:0*
T0*'
_output_shapes
:���������2	
Softmaxl
IdentityIdentitySoftmax:softmax:0^NoOp*
T0*'
_output_shapes
:���������2

Identity
NoOpNoOp^BiasAdd/ReadVariableOp^MatMul/ReadVariableOp*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime**
_input_shapes
:���������	: : 20
BiasAdd/ReadVariableOpBiasAdd/ReadVariableOp2.
MatMul/ReadVariableOpMatMul/ReadVariableOp:O K
'
_output_shapes
:���������	
 
_user_specified_nameinputs
�
�
*__inference_4_dense32_layer_call_fn_926056

inputs
unknown:@ 
	unknown_0: 
identity��StatefulPartitionedCall�
StatefulPartitionedCallStatefulPartitionedCallinputsunknown	unknown_0*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:��������� *$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *N
fIRG
E__inference_4_dense32_layer_call_and_return_conditional_losses_9253882
StatefulPartitionedCall{
IdentityIdentity StatefulPartitionedCall:output:0^NoOp*
T0*'
_output_shapes
:��������� 2

Identityh
NoOpNoOp^StatefulPartitionedCall*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime**
_input_shapes
:���������@: : 22
StatefulPartitionedCallStatefulPartitionedCall:O K
'
_output_shapes
:���������@
 
_user_specified_nameinputs
�
�
E__inference_5_dense18_layer_call_and_return_conditional_losses_925405

inputs0
matmul_readvariableop_resource: -
biasadd_readvariableop_resource:
identity��BiasAdd/ReadVariableOp�MatMul/ReadVariableOp�
MatMul/ReadVariableOpReadVariableOpmatmul_readvariableop_resource*
_output_shapes

: *
dtype02
MatMul/ReadVariableOps
MatMulMatMulinputsMatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2
MatMul�
BiasAdd/ReadVariableOpReadVariableOpbiasadd_readvariableop_resource*
_output_shapes
:*
dtype02
BiasAdd/ReadVariableOp�
BiasAddBiasAddMatMul:product:0BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2	
BiasAddX
ReluReluBiasAdd:output:0*
T0*'
_output_shapes
:���������2
Relum
IdentityIdentityRelu:activations:0^NoOp*
T0*'
_output_shapes
:���������2

Identity
NoOpNoOp^BiasAdd/ReadVariableOp^MatMul/ReadVariableOp*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime**
_input_shapes
:��������� : : 20
BiasAdd/ReadVariableOpBiasAdd/ReadVariableOp2.
MatMul/ReadVariableOpMatMul/ReadVariableOp:O K
'
_output_shapes
:��������� 
 
_user_specified_nameinputs
�
�
E__inference_5_dense18_layer_call_and_return_conditional_losses_926067

inputs0
matmul_readvariableop_resource: -
biasadd_readvariableop_resource:
identity��BiasAdd/ReadVariableOp�MatMul/ReadVariableOp�
MatMul/ReadVariableOpReadVariableOpmatmul_readvariableop_resource*
_output_shapes

: *
dtype02
MatMul/ReadVariableOps
MatMulMatMulinputsMatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2
MatMul�
BiasAdd/ReadVariableOpReadVariableOpbiasadd_readvariableop_resource*
_output_shapes
:*
dtype02
BiasAdd/ReadVariableOp�
BiasAddBiasAddMatMul:product:0BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2	
BiasAddX
ReluReluBiasAdd:output:0*
T0*'
_output_shapes
:���������2
Relum
IdentityIdentityRelu:activations:0^NoOp*
T0*'
_output_shapes
:���������2

Identity
NoOpNoOp^BiasAdd/ReadVariableOp^MatMul/ReadVariableOp*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime**
_input_shapes
:��������� : : 20
BiasAdd/ReadVariableOpBiasAdd/ReadVariableOp2.
MatMul/ReadVariableOpMatMul/ReadVariableOp:O K
'
_output_shapes
:��������� 
 
_user_specified_nameinputs
�
�
E__inference_4_dense32_layer_call_and_return_conditional_losses_926047

inputs0
matmul_readvariableop_resource:@ -
biasadd_readvariableop_resource: 
identity��BiasAdd/ReadVariableOp�MatMul/ReadVariableOp�
MatMul/ReadVariableOpReadVariableOpmatmul_readvariableop_resource*
_output_shapes

:@ *
dtype02
MatMul/ReadVariableOps
MatMulMatMulinputsMatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:��������� 2
MatMul�
BiasAdd/ReadVariableOpReadVariableOpbiasadd_readvariableop_resource*
_output_shapes
: *
dtype02
BiasAdd/ReadVariableOp�
BiasAddBiasAddMatMul:product:0BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:��������� 2	
BiasAddX
ReluReluBiasAdd:output:0*
T0*'
_output_shapes
:��������� 2
Relum
IdentityIdentityRelu:activations:0^NoOp*
T0*'
_output_shapes
:��������� 2

Identity
NoOpNoOp^BiasAdd/ReadVariableOp^MatMul/ReadVariableOp*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime**
_input_shapes
:���������@: : 20
BiasAdd/ReadVariableOpBiasAdd/ReadVariableOp2.
MatMul/ReadVariableOpMatMul/ReadVariableOp:O K
'
_output_shapes
:���������@
 
_user_specified_nameinputs
�
�
E__inference_3_dense64_layer_call_and_return_conditional_losses_926027

inputs0
matmul_readvariableop_resource: @-
biasadd_readvariableop_resource:@
identity��BiasAdd/ReadVariableOp�MatMul/ReadVariableOp�
MatMul/ReadVariableOpReadVariableOpmatmul_readvariableop_resource*
_output_shapes

: @*
dtype02
MatMul/ReadVariableOps
MatMulMatMulinputsMatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������@2
MatMul�
BiasAdd/ReadVariableOpReadVariableOpbiasadd_readvariableop_resource*
_output_shapes
:@*
dtype02
BiasAdd/ReadVariableOp�
BiasAddBiasAddMatMul:product:0BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������@2	
BiasAddX
ReluReluBiasAdd:output:0*
T0*'
_output_shapes
:���������@2
Relum
IdentityIdentityRelu:activations:0^NoOp*
T0*'
_output_shapes
:���������@2

Identity
NoOpNoOp^BiasAdd/ReadVariableOp^MatMul/ReadVariableOp*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime**
_input_shapes
:��������� : : 20
BiasAdd/ReadVariableOpBiasAdd/ReadVariableOp2.
MatMul/ReadVariableOpMatMul/ReadVariableOp:O K
'
_output_shapes
:��������� 
 
_user_specified_nameinputs
�
�
*__inference_2_dense32_layer_call_fn_926016

inputs
unknown: 
	unknown_0: 
identity��StatefulPartitionedCall�
StatefulPartitionedCallStatefulPartitionedCallinputsunknown	unknown_0*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:��������� *$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *N
fIRG
E__inference_2_dense32_layer_call_and_return_conditional_losses_9253542
StatefulPartitionedCall{
IdentityIdentity StatefulPartitionedCall:output:0^NoOp*
T0*'
_output_shapes
:��������� 2

Identityh
NoOpNoOp^StatefulPartitionedCall*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime**
_input_shapes
:���������: : 22
StatefulPartitionedCallStatefulPartitionedCall:O K
'
_output_shapes
:���������
 
_user_specified_nameinputs
�
�
*__inference_5_dense18_layer_call_fn_926076

inputs
unknown: 
	unknown_0:
identity��StatefulPartitionedCall�
StatefulPartitionedCallStatefulPartitionedCallinputsunknown	unknown_0*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������*$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *N
fIRG
E__inference_5_dense18_layer_call_and_return_conditional_losses_9254052
StatefulPartitionedCall{
IdentityIdentity StatefulPartitionedCall:output:0^NoOp*
T0*'
_output_shapes
:���������2

Identityh
NoOpNoOp^StatefulPartitionedCall*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime**
_input_shapes
:��������� : : 22
StatefulPartitionedCallStatefulPartitionedCall:O K
'
_output_shapes
:��������� 
 
_user_specified_nameinputs
�
�
E__inference_2_dense32_layer_call_and_return_conditional_losses_925354

inputs0
matmul_readvariableop_resource: -
biasadd_readvariableop_resource: 
identity��BiasAdd/ReadVariableOp�MatMul/ReadVariableOp�
MatMul/ReadVariableOpReadVariableOpmatmul_readvariableop_resource*
_output_shapes

: *
dtype02
MatMul/ReadVariableOps
MatMulMatMulinputsMatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:��������� 2
MatMul�
BiasAdd/ReadVariableOpReadVariableOpbiasadd_readvariableop_resource*
_output_shapes
: *
dtype02
BiasAdd/ReadVariableOp�
BiasAddBiasAddMatMul:product:0BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:��������� 2	
BiasAddX
ReluReluBiasAdd:output:0*
T0*'
_output_shapes
:��������� 2
Relum
IdentityIdentityRelu:activations:0^NoOp*
T0*'
_output_shapes
:��������� 2

Identity
NoOpNoOp^BiasAdd/ReadVariableOp^MatMul/ReadVariableOp*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime**
_input_shapes
:���������: : 20
BiasAdd/ReadVariableOpBiasAdd/ReadVariableOp2.
MatMul/ReadVariableOpMatMul/ReadVariableOp:O K
'
_output_shapes
:���������
 
_user_specified_nameinputs
�
�
E__inference_3_dense64_layer_call_and_return_conditional_losses_925371

inputs0
matmul_readvariableop_resource: @-
biasadd_readvariableop_resource:@
identity��BiasAdd/ReadVariableOp�MatMul/ReadVariableOp�
MatMul/ReadVariableOpReadVariableOpmatmul_readvariableop_resource*
_output_shapes

: @*
dtype02
MatMul/ReadVariableOps
MatMulMatMulinputsMatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������@2
MatMul�
BiasAdd/ReadVariableOpReadVariableOpbiasadd_readvariableop_resource*
_output_shapes
:@*
dtype02
BiasAdd/ReadVariableOp�
BiasAddBiasAddMatMul:product:0BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������@2	
BiasAddX
ReluReluBiasAdd:output:0*
T0*'
_output_shapes
:���������@2
Relum
IdentityIdentityRelu:activations:0^NoOp*
T0*'
_output_shapes
:���������@2

Identity
NoOpNoOp^BiasAdd/ReadVariableOp^MatMul/ReadVariableOp*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime**
_input_shapes
:��������� : : 20
BiasAdd/ReadVariableOpBiasAdd/ReadVariableOp2.
MatMul/ReadVariableOpMatMul/ReadVariableOp:O K
'
_output_shapes
:��������� 
 
_user_specified_nameinputs
�
�
$__inference_signature_wrapper_925804
hst_jobs
unknown:	
	unknown_0:
	unknown_1: 
	unknown_2: 
	unknown_3: @
	unknown_4:@
	unknown_5:@ 
	unknown_6: 
	unknown_7: 
	unknown_8:
	unknown_9:	

unknown_10:	

unknown_11:	

unknown_12:
identity��StatefulPartitionedCall�
StatefulPartitionedCallStatefulPartitionedCallhst_jobsunknown	unknown_0	unknown_1	unknown_2	unknown_3	unknown_4	unknown_5	unknown_6	unknown_7	unknown_8	unknown_9
unknown_10
unknown_11
unknown_12*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������*0
_read_only_resource_inputs
	
*-
config_proto

CPU

GPU 2J 8� **
f%R#
!__inference__wrapped_model_9253192
StatefulPartitionedCall{
IdentityIdentity StatefulPartitionedCall:output:0^NoOp*
T0*'
_output_shapes
:���������2

Identityh
NoOpNoOp^StatefulPartitionedCall*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime*B
_input_shapes1
/:���������	: : : : : : : : : : : : : : 22
StatefulPartitionedCallStatefulPartitionedCall:Q M
'
_output_shapes
:���������	
"
_user_specified_name
hst_jobs
�h
�
__inference__traced_save_926292
file_prefix/
+savev2_1_dense18_kernel_read_readvariableop-
)savev2_1_dense18_bias_read_readvariableop/
+savev2_2_dense32_kernel_read_readvariableop-
)savev2_2_dense32_bias_read_readvariableop/
+savev2_3_dense64_kernel_read_readvariableop-
)savev2_3_dense64_bias_read_readvariableop/
+savev2_4_dense32_kernel_read_readvariableop-
)savev2_4_dense32_bias_read_readvariableop/
+savev2_5_dense18_kernel_read_readvariableop-
)savev2_5_dense18_bias_read_readvariableop.
*savev2_6_dense9_kernel_read_readvariableop,
(savev2_6_dense9_bias_read_readvariableop4
0savev2_output_mem_clf_kernel_read_readvariableop2
.savev2_output_mem_clf_bias_read_readvariableop(
$savev2_adam_iter_read_readvariableop	*
&savev2_adam_beta_1_read_readvariableop*
&savev2_adam_beta_2_read_readvariableop)
%savev2_adam_decay_read_readvariableop1
-savev2_adam_learning_rate_read_readvariableop$
 savev2_total_read_readvariableop$
 savev2_count_read_readvariableop&
"savev2_total_1_read_readvariableop&
"savev2_count_1_read_readvariableop6
2savev2_adam_1_dense18_kernel_m_read_readvariableop4
0savev2_adam_1_dense18_bias_m_read_readvariableop6
2savev2_adam_2_dense32_kernel_m_read_readvariableop4
0savev2_adam_2_dense32_bias_m_read_readvariableop6
2savev2_adam_3_dense64_kernel_m_read_readvariableop4
0savev2_adam_3_dense64_bias_m_read_readvariableop6
2savev2_adam_4_dense32_kernel_m_read_readvariableop4
0savev2_adam_4_dense32_bias_m_read_readvariableop6
2savev2_adam_5_dense18_kernel_m_read_readvariableop4
0savev2_adam_5_dense18_bias_m_read_readvariableop5
1savev2_adam_6_dense9_kernel_m_read_readvariableop3
/savev2_adam_6_dense9_bias_m_read_readvariableop;
7savev2_adam_output_mem_clf_kernel_m_read_readvariableop9
5savev2_adam_output_mem_clf_bias_m_read_readvariableop6
2savev2_adam_1_dense18_kernel_v_read_readvariableop4
0savev2_adam_1_dense18_bias_v_read_readvariableop6
2savev2_adam_2_dense32_kernel_v_read_readvariableop4
0savev2_adam_2_dense32_bias_v_read_readvariableop6
2savev2_adam_3_dense64_kernel_v_read_readvariableop4
0savev2_adam_3_dense64_bias_v_read_readvariableop6
2savev2_adam_4_dense32_kernel_v_read_readvariableop4
0savev2_adam_4_dense32_bias_v_read_readvariableop6
2savev2_adam_5_dense18_kernel_v_read_readvariableop4
0savev2_adam_5_dense18_bias_v_read_readvariableop5
1savev2_adam_6_dense9_kernel_v_read_readvariableop3
/savev2_adam_6_dense9_bias_v_read_readvariableop;
7savev2_adam_output_mem_clf_kernel_v_read_readvariableop9
5savev2_adam_output_mem_clf_bias_v_read_readvariableop
savev2_const

identity_1��MergeV2Checkpoints�
StaticRegexFullMatchStaticRegexFullMatchfile_prefix"/device:CPU:**
_output_shapes
: *
pattern
^s3://.*2
StaticRegexFullMatchc
ConstConst"/device:CPU:**
_output_shapes
: *
dtype0*
valueB B.part2
Constl
Const_1Const"/device:CPU:**
_output_shapes
: *
dtype0*
valueB B
_temp/part2	
Const_1�
SelectSelectStaticRegexFullMatch:output:0Const:output:0Const_1:output:0"/device:CPU:**
T0*
_output_shapes
: 2
Selectt

StringJoin
StringJoinfile_prefixSelect:output:0"/device:CPU:**
N*
_output_shapes
: 2

StringJoinZ

num_shardsConst*
_output_shapes
: *
dtype0*
value	B :2

num_shards
ShardedFilename/shardConst"/device:CPU:0*
_output_shapes
: *
dtype0*
value	B : 2
ShardedFilename/shard�
ShardedFilenameShardedFilenameStringJoin:output:0ShardedFilename/shard:output:0num_shards:output:0"/device:CPU:0*
_output_shapes
: 2
ShardedFilename�
SaveV2/tensor_namesConst"/device:CPU:0*
_output_shapes
:4*
dtype0*�
value�B�4B6layer_with_weights-0/kernel/.ATTRIBUTES/VARIABLE_VALUEB4layer_with_weights-0/bias/.ATTRIBUTES/VARIABLE_VALUEB6layer_with_weights-1/kernel/.ATTRIBUTES/VARIABLE_VALUEB4layer_with_weights-1/bias/.ATTRIBUTES/VARIABLE_VALUEB6layer_with_weights-2/kernel/.ATTRIBUTES/VARIABLE_VALUEB4layer_with_weights-2/bias/.ATTRIBUTES/VARIABLE_VALUEB6layer_with_weights-3/kernel/.ATTRIBUTES/VARIABLE_VALUEB4layer_with_weights-3/bias/.ATTRIBUTES/VARIABLE_VALUEB6layer_with_weights-4/kernel/.ATTRIBUTES/VARIABLE_VALUEB4layer_with_weights-4/bias/.ATTRIBUTES/VARIABLE_VALUEB6layer_with_weights-5/kernel/.ATTRIBUTES/VARIABLE_VALUEB4layer_with_weights-5/bias/.ATTRIBUTES/VARIABLE_VALUEB6layer_with_weights-6/kernel/.ATTRIBUTES/VARIABLE_VALUEB4layer_with_weights-6/bias/.ATTRIBUTES/VARIABLE_VALUEB)optimizer/iter/.ATTRIBUTES/VARIABLE_VALUEB+optimizer/beta_1/.ATTRIBUTES/VARIABLE_VALUEB+optimizer/beta_2/.ATTRIBUTES/VARIABLE_VALUEB*optimizer/decay/.ATTRIBUTES/VARIABLE_VALUEB2optimizer/learning_rate/.ATTRIBUTES/VARIABLE_VALUEB4keras_api/metrics/0/total/.ATTRIBUTES/VARIABLE_VALUEB4keras_api/metrics/0/count/.ATTRIBUTES/VARIABLE_VALUEB4keras_api/metrics/1/total/.ATTRIBUTES/VARIABLE_VALUEB4keras_api/metrics/1/count/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-0/kernel/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-0/bias/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-1/kernel/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-1/bias/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-2/kernel/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-2/bias/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-3/kernel/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-3/bias/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-4/kernel/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-4/bias/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-5/kernel/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-5/bias/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-6/kernel/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-6/bias/.OPTIMIZER_SLOT/optimizer/m/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-0/kernel/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-0/bias/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-1/kernel/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-1/bias/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-2/kernel/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-2/bias/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-3/kernel/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-3/bias/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-4/kernel/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-4/bias/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-5/kernel/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-5/bias/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEBRlayer_with_weights-6/kernel/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEBPlayer_with_weights-6/bias/.OPTIMIZER_SLOT/optimizer/v/.ATTRIBUTES/VARIABLE_VALUEB_CHECKPOINTABLE_OBJECT_GRAPH2
SaveV2/tensor_names�
SaveV2/shape_and_slicesConst"/device:CPU:0*
_output_shapes
:4*
dtype0*{
valuerBp4B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B B 2
SaveV2/shape_and_slices�
SaveV2SaveV2ShardedFilename:filename:0SaveV2/tensor_names:output:0 SaveV2/shape_and_slices:output:0+savev2_1_dense18_kernel_read_readvariableop)savev2_1_dense18_bias_read_readvariableop+savev2_2_dense32_kernel_read_readvariableop)savev2_2_dense32_bias_read_readvariableop+savev2_3_dense64_kernel_read_readvariableop)savev2_3_dense64_bias_read_readvariableop+savev2_4_dense32_kernel_read_readvariableop)savev2_4_dense32_bias_read_readvariableop+savev2_5_dense18_kernel_read_readvariableop)savev2_5_dense18_bias_read_readvariableop*savev2_6_dense9_kernel_read_readvariableop(savev2_6_dense9_bias_read_readvariableop0savev2_output_mem_clf_kernel_read_readvariableop.savev2_output_mem_clf_bias_read_readvariableop$savev2_adam_iter_read_readvariableop&savev2_adam_beta_1_read_readvariableop&savev2_adam_beta_2_read_readvariableop%savev2_adam_decay_read_readvariableop-savev2_adam_learning_rate_read_readvariableop savev2_total_read_readvariableop savev2_count_read_readvariableop"savev2_total_1_read_readvariableop"savev2_count_1_read_readvariableop2savev2_adam_1_dense18_kernel_m_read_readvariableop0savev2_adam_1_dense18_bias_m_read_readvariableop2savev2_adam_2_dense32_kernel_m_read_readvariableop0savev2_adam_2_dense32_bias_m_read_readvariableop2savev2_adam_3_dense64_kernel_m_read_readvariableop0savev2_adam_3_dense64_bias_m_read_readvariableop2savev2_adam_4_dense32_kernel_m_read_readvariableop0savev2_adam_4_dense32_bias_m_read_readvariableop2savev2_adam_5_dense18_kernel_m_read_readvariableop0savev2_adam_5_dense18_bias_m_read_readvariableop1savev2_adam_6_dense9_kernel_m_read_readvariableop/savev2_adam_6_dense9_bias_m_read_readvariableop7savev2_adam_output_mem_clf_kernel_m_read_readvariableop5savev2_adam_output_mem_clf_bias_m_read_readvariableop2savev2_adam_1_dense18_kernel_v_read_readvariableop0savev2_adam_1_dense18_bias_v_read_readvariableop2savev2_adam_2_dense32_kernel_v_read_readvariableop0savev2_adam_2_dense32_bias_v_read_readvariableop2savev2_adam_3_dense64_kernel_v_read_readvariableop0savev2_adam_3_dense64_bias_v_read_readvariableop2savev2_adam_4_dense32_kernel_v_read_readvariableop0savev2_adam_4_dense32_bias_v_read_readvariableop2savev2_adam_5_dense18_kernel_v_read_readvariableop0savev2_adam_5_dense18_bias_v_read_readvariableop1savev2_adam_6_dense9_kernel_v_read_readvariableop/savev2_adam_6_dense9_bias_v_read_readvariableop7savev2_adam_output_mem_clf_kernel_v_read_readvariableop5savev2_adam_output_mem_clf_bias_v_read_readvariableopsavev2_const"/device:CPU:0*
_output_shapes
 *B
dtypes8
624	2
SaveV2�
&MergeV2Checkpoints/checkpoint_prefixesPackShardedFilename:filename:0^SaveV2"/device:CPU:0*
N*
T0*
_output_shapes
:2(
&MergeV2Checkpoints/checkpoint_prefixes�
MergeV2CheckpointsMergeV2Checkpoints/MergeV2Checkpoints/checkpoint_prefixes:output:0file_prefix"/device:CPU:0*
_output_shapes
 2
MergeV2Checkpointsr
IdentityIdentityfile_prefix^MergeV2Checkpoints"/device:CPU:0*
T0*
_output_shapes
: 2

Identity_

Identity_1IdentityIdentity:output:0^NoOp*
T0*
_output_shapes
: 2

Identity_1c
NoOpNoOp^MergeV2Checkpoints*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"!

identity_1Identity_1:output:0*�
_input_shapes�
�: :	:: : : @:@:@ : : ::	:	:	:: : : : : : : : : :	:: : : @:@:@ : : ::	:	:	::	:: : : @:@:@ : : ::	:	:	:: 2(
MergeV2CheckpointsMergeV2Checkpoints:C ?

_output_shapes
: 
%
_user_specified_namefile_prefix:$ 

_output_shapes

:	: 

_output_shapes
::$ 

_output_shapes

: : 

_output_shapes
: :$ 

_output_shapes

: @: 

_output_shapes
:@:$ 

_output_shapes

:@ : 

_output_shapes
: :$	 

_output_shapes

: : 


_output_shapes
::$ 

_output_shapes

:	: 

_output_shapes
:	:$ 

_output_shapes

:	: 

_output_shapes
::

_output_shapes
: :

_output_shapes
: :

_output_shapes
: :

_output_shapes
: :

_output_shapes
: :

_output_shapes
: :

_output_shapes
: :

_output_shapes
: :

_output_shapes
: :$ 

_output_shapes

:	: 

_output_shapes
::$ 

_output_shapes

: : 

_output_shapes
: :$ 

_output_shapes

: @: 

_output_shapes
:@:$ 

_output_shapes

:@ : 

_output_shapes
: :$  

_output_shapes

: : !

_output_shapes
::$" 

_output_shapes

:	: #

_output_shapes
:	:$$ 

_output_shapes

:	: %

_output_shapes
::$& 

_output_shapes

:	: '

_output_shapes
::$( 

_output_shapes

: : )

_output_shapes
: :$* 

_output_shapes

: @: +

_output_shapes
:@:$, 

_output_shapes

:@ : -

_output_shapes
: :$. 

_output_shapes

: : /

_output_shapes
::$0 

_output_shapes

:	: 1

_output_shapes
:	:$2 

_output_shapes

:	: 3

_output_shapes
::4

_output_shapes
: 
�(
�
M__inference_memory_classifier_layer_call_and_return_conditional_losses_925446

inputs 
dense18_925338:	
dense18_925340: 
dense32_925355: 
dense32_925357:  
dense64_925372: @
dense64_925374:@ 
dense32_925389:@ 
dense32_925391:  
dense18_925406: 
dense18_925408:
dense9_925423:	
dense9_925425:	'
output_mem_clf_925440:	#
output_mem_clf_925442:
identity��!1_dense18/StatefulPartitionedCall�!2_dense32/StatefulPartitionedCall�!3_dense64/StatefulPartitionedCall�!4_dense32/StatefulPartitionedCall�!5_dense18/StatefulPartitionedCall� 6_dense9/StatefulPartitionedCall�&output_mem_clf/StatefulPartitionedCall�
!1_dense18/StatefulPartitionedCallStatefulPartitionedCallinputsdense18_925338dense18_925340*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������*$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *N
fIRG
E__inference_1_dense18_layer_call_and_return_conditional_losses_9253372#
!1_dense18/StatefulPartitionedCall�
!2_dense32/StatefulPartitionedCallStatefulPartitionedCall*1_dense18/StatefulPartitionedCall:output:0dense32_925355dense32_925357*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:��������� *$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *N
fIRG
E__inference_2_dense32_layer_call_and_return_conditional_losses_9253542#
!2_dense32/StatefulPartitionedCall�
!3_dense64/StatefulPartitionedCallStatefulPartitionedCall*2_dense32/StatefulPartitionedCall:output:0dense64_925372dense64_925374*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������@*$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *N
fIRG
E__inference_3_dense64_layer_call_and_return_conditional_losses_9253712#
!3_dense64/StatefulPartitionedCall�
!4_dense32/StatefulPartitionedCallStatefulPartitionedCall*3_dense64/StatefulPartitionedCall:output:0dense32_925389dense32_925391*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:��������� *$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *N
fIRG
E__inference_4_dense32_layer_call_and_return_conditional_losses_9253882#
!4_dense32/StatefulPartitionedCall�
!5_dense18/StatefulPartitionedCallStatefulPartitionedCall*4_dense32/StatefulPartitionedCall:output:0dense18_925406dense18_925408*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������*$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *N
fIRG
E__inference_5_dense18_layer_call_and_return_conditional_losses_9254052#
!5_dense18/StatefulPartitionedCall�
 6_dense9/StatefulPartitionedCallStatefulPartitionedCall*5_dense18/StatefulPartitionedCall:output:0dense9_925423dense9_925425*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������	*$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *M
fHRF
D__inference_6_dense9_layer_call_and_return_conditional_losses_9254222"
 6_dense9/StatefulPartitionedCall�
&output_mem_clf/StatefulPartitionedCallStatefulPartitionedCall)6_dense9/StatefulPartitionedCall:output:0output_mem_clf_925440output_mem_clf_925442*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������*$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *S
fNRL
J__inference_output_mem_clf_layer_call_and_return_conditional_losses_9254392(
&output_mem_clf/StatefulPartitionedCall�
IdentityIdentity/output_mem_clf/StatefulPartitionedCall:output:0^NoOp*
T0*'
_output_shapes
:���������2

Identity�
NoOpNoOp"^1_dense18/StatefulPartitionedCall"^2_dense32/StatefulPartitionedCall"^3_dense64/StatefulPartitionedCall"^4_dense32/StatefulPartitionedCall"^5_dense18/StatefulPartitionedCall!^6_dense9/StatefulPartitionedCall'^output_mem_clf/StatefulPartitionedCall*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime*B
_input_shapes1
/:���������	: : : : : : : : : : : : : : 2F
!1_dense18/StatefulPartitionedCall!1_dense18/StatefulPartitionedCall2F
!2_dense32/StatefulPartitionedCall!2_dense32/StatefulPartitionedCall2F
!3_dense64/StatefulPartitionedCall!3_dense64/StatefulPartitionedCall2F
!4_dense32/StatefulPartitionedCall!4_dense32/StatefulPartitionedCall2F
!5_dense18/StatefulPartitionedCall!5_dense18/StatefulPartitionedCall2D
 6_dense9/StatefulPartitionedCall 6_dense9/StatefulPartitionedCall2P
&output_mem_clf/StatefulPartitionedCall&output_mem_clf/StatefulPartitionedCall:O K
'
_output_shapes
:���������	
 
_user_specified_nameinputs
�(
�
M__inference_memory_classifier_layer_call_and_return_conditional_losses_925763
hst_jobs 
dense18_925727:	
dense18_925729: 
dense32_925732: 
dense32_925734:  
dense64_925737: @
dense64_925739:@ 
dense32_925742:@ 
dense32_925744:  
dense18_925747: 
dense18_925749:
dense9_925752:	
dense9_925754:	'
output_mem_clf_925757:	#
output_mem_clf_925759:
identity��!1_dense18/StatefulPartitionedCall�!2_dense32/StatefulPartitionedCall�!3_dense64/StatefulPartitionedCall�!4_dense32/StatefulPartitionedCall�!5_dense18/StatefulPartitionedCall� 6_dense9/StatefulPartitionedCall�&output_mem_clf/StatefulPartitionedCall�
!1_dense18/StatefulPartitionedCallStatefulPartitionedCallhst_jobsdense18_925727dense18_925729*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������*$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *N
fIRG
E__inference_1_dense18_layer_call_and_return_conditional_losses_9253372#
!1_dense18/StatefulPartitionedCall�
!2_dense32/StatefulPartitionedCallStatefulPartitionedCall*1_dense18/StatefulPartitionedCall:output:0dense32_925732dense32_925734*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:��������� *$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *N
fIRG
E__inference_2_dense32_layer_call_and_return_conditional_losses_9253542#
!2_dense32/StatefulPartitionedCall�
!3_dense64/StatefulPartitionedCallStatefulPartitionedCall*2_dense32/StatefulPartitionedCall:output:0dense64_925737dense64_925739*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������@*$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *N
fIRG
E__inference_3_dense64_layer_call_and_return_conditional_losses_9253712#
!3_dense64/StatefulPartitionedCall�
!4_dense32/StatefulPartitionedCallStatefulPartitionedCall*3_dense64/StatefulPartitionedCall:output:0dense32_925742dense32_925744*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:��������� *$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *N
fIRG
E__inference_4_dense32_layer_call_and_return_conditional_losses_9253882#
!4_dense32/StatefulPartitionedCall�
!5_dense18/StatefulPartitionedCallStatefulPartitionedCall*4_dense32/StatefulPartitionedCall:output:0dense18_925747dense18_925749*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������*$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *N
fIRG
E__inference_5_dense18_layer_call_and_return_conditional_losses_9254052#
!5_dense18/StatefulPartitionedCall�
 6_dense9/StatefulPartitionedCallStatefulPartitionedCall*5_dense18/StatefulPartitionedCall:output:0dense9_925752dense9_925754*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������	*$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *M
fHRF
D__inference_6_dense9_layer_call_and_return_conditional_losses_9254222"
 6_dense9/StatefulPartitionedCall�
&output_mem_clf/StatefulPartitionedCallStatefulPartitionedCall)6_dense9/StatefulPartitionedCall:output:0output_mem_clf_925757output_mem_clf_925759*
Tin
2*
Tout
2*
_collective_manager_ids
 *'
_output_shapes
:���������*$
_read_only_resource_inputs
*-
config_proto

CPU

GPU 2J 8� *S
fNRL
J__inference_output_mem_clf_layer_call_and_return_conditional_losses_9254392(
&output_mem_clf/StatefulPartitionedCall�
IdentityIdentity/output_mem_clf/StatefulPartitionedCall:output:0^NoOp*
T0*'
_output_shapes
:���������2

Identity�
NoOpNoOp"^1_dense18/StatefulPartitionedCall"^2_dense32/StatefulPartitionedCall"^3_dense64/StatefulPartitionedCall"^4_dense32/StatefulPartitionedCall"^5_dense18/StatefulPartitionedCall!^6_dense9/StatefulPartitionedCall'^output_mem_clf/StatefulPartitionedCall*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime*B
_input_shapes1
/:���������	: : : : : : : : : : : : : : 2F
!1_dense18/StatefulPartitionedCall!1_dense18/StatefulPartitionedCall2F
!2_dense32/StatefulPartitionedCall!2_dense32/StatefulPartitionedCall2F
!3_dense64/StatefulPartitionedCall!3_dense64/StatefulPartitionedCall2F
!4_dense32/StatefulPartitionedCall!4_dense32/StatefulPartitionedCall2F
!5_dense18/StatefulPartitionedCall!5_dense18/StatefulPartitionedCall2D
 6_dense9/StatefulPartitionedCall 6_dense9/StatefulPartitionedCall2P
&output_mem_clf/StatefulPartitionedCall&output_mem_clf/StatefulPartitionedCall:Q M
'
_output_shapes
:���������	
"
_user_specified_name
hst_jobs
�
�
E__inference_2_dense32_layer_call_and_return_conditional_losses_926007

inputs0
matmul_readvariableop_resource: -
biasadd_readvariableop_resource: 
identity��BiasAdd/ReadVariableOp�MatMul/ReadVariableOp�
MatMul/ReadVariableOpReadVariableOpmatmul_readvariableop_resource*
_output_shapes

: *
dtype02
MatMul/ReadVariableOps
MatMulMatMulinputsMatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:��������� 2
MatMul�
BiasAdd/ReadVariableOpReadVariableOpbiasadd_readvariableop_resource*
_output_shapes
: *
dtype02
BiasAdd/ReadVariableOp�
BiasAddBiasAddMatMul:product:0BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:��������� 2	
BiasAddX
ReluReluBiasAdd:output:0*
T0*'
_output_shapes
:��������� 2
Relum
IdentityIdentityRelu:activations:0^NoOp*
T0*'
_output_shapes
:��������� 2

Identity
NoOpNoOp^BiasAdd/ReadVariableOp^MatMul/ReadVariableOp*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime**
_input_shapes
:���������: : 20
BiasAdd/ReadVariableOpBiasAdd/ReadVariableOp2.
MatMul/ReadVariableOpMatMul/ReadVariableOp:O K
'
_output_shapes
:���������
 
_user_specified_nameinputs
�
�
D__inference_6_dense9_layer_call_and_return_conditional_losses_925422

inputs0
matmul_readvariableop_resource:	-
biasadd_readvariableop_resource:	
identity��BiasAdd/ReadVariableOp�MatMul/ReadVariableOp�
MatMul/ReadVariableOpReadVariableOpmatmul_readvariableop_resource*
_output_shapes

:	*
dtype02
MatMul/ReadVariableOps
MatMulMatMulinputsMatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������	2
MatMul�
BiasAdd/ReadVariableOpReadVariableOpbiasadd_readvariableop_resource*
_output_shapes
:	*
dtype02
BiasAdd/ReadVariableOp�
BiasAddBiasAddMatMul:product:0BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������	2	
BiasAddX
ReluReluBiasAdd:output:0*
T0*'
_output_shapes
:���������	2
Relum
IdentityIdentityRelu:activations:0^NoOp*
T0*'
_output_shapes
:���������	2

Identity
NoOpNoOp^BiasAdd/ReadVariableOp^MatMul/ReadVariableOp*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime**
_input_shapes
:���������: : 20
BiasAdd/ReadVariableOpBiasAdd/ReadVariableOp2.
MatMul/ReadVariableOpMatMul/ReadVariableOp:O K
'
_output_shapes
:���������
 
_user_specified_nameinputs
�F
�
M__inference_memory_classifier_layer_call_and_return_conditional_losses_925910

inputs8
&dense18_matmul_readvariableop_resource:	5
'dense18_biasadd_readvariableop_resource:8
&dense32_matmul_readvariableop_resource: 5
'dense32_biasadd_readvariableop_resource: 8
&dense64_matmul_readvariableop_resource: @5
'dense64_biasadd_readvariableop_resource:@:
(dense32_matmul_readvariableop_resource_0:@ 7
)dense32_biasadd_readvariableop_resource_0: :
(dense18_matmul_readvariableop_resource_0: 7
)dense18_biasadd_readvariableop_resource_0:7
%dense9_matmul_readvariableop_resource:	4
&dense9_biasadd_readvariableop_resource:	?
-output_mem_clf_matmul_readvariableop_resource:	<
.output_mem_clf_biasadd_readvariableop_resource:
identity�� 1_dense18/BiasAdd/ReadVariableOp�1_dense18/MatMul/ReadVariableOp� 2_dense32/BiasAdd/ReadVariableOp�2_dense32/MatMul/ReadVariableOp� 3_dense64/BiasAdd/ReadVariableOp�3_dense64/MatMul/ReadVariableOp� 4_dense32/BiasAdd/ReadVariableOp�4_dense32/MatMul/ReadVariableOp� 5_dense18/BiasAdd/ReadVariableOp�5_dense18/MatMul/ReadVariableOp�6_dense9/BiasAdd/ReadVariableOp�6_dense9/MatMul/ReadVariableOp�%output_mem_clf/BiasAdd/ReadVariableOp�$output_mem_clf/MatMul/ReadVariableOp�
1_dense18/MatMul/ReadVariableOpReadVariableOp&dense18_matmul_readvariableop_resource*
_output_shapes

:	*
dtype02!
1_dense18/MatMul/ReadVariableOp�
1_dense18/MatMulMatMulinputs'1_dense18/MatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2
1_dense18/MatMul�
 1_dense18/BiasAdd/ReadVariableOpReadVariableOp'dense18_biasadd_readvariableop_resource*
_output_shapes
:*
dtype02"
 1_dense18/BiasAdd/ReadVariableOp�
1_dense18/BiasAddBiasAdd1_dense18/MatMul:product:0(1_dense18/BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2
1_dense18/BiasAddv
1_dense18/ReluRelu1_dense18/BiasAdd:output:0*
T0*'
_output_shapes
:���������2
1_dense18/Relu�
2_dense32/MatMul/ReadVariableOpReadVariableOp&dense32_matmul_readvariableop_resource*
_output_shapes

: *
dtype02!
2_dense32/MatMul/ReadVariableOp�
2_dense32/MatMulMatMul1_dense18/Relu:activations:0'2_dense32/MatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:��������� 2
2_dense32/MatMul�
 2_dense32/BiasAdd/ReadVariableOpReadVariableOp'dense32_biasadd_readvariableop_resource*
_output_shapes
: *
dtype02"
 2_dense32/BiasAdd/ReadVariableOp�
2_dense32/BiasAddBiasAdd2_dense32/MatMul:product:0(2_dense32/BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:��������� 2
2_dense32/BiasAddv
2_dense32/ReluRelu2_dense32/BiasAdd:output:0*
T0*'
_output_shapes
:��������� 2
2_dense32/Relu�
3_dense64/MatMul/ReadVariableOpReadVariableOp&dense64_matmul_readvariableop_resource*
_output_shapes

: @*
dtype02!
3_dense64/MatMul/ReadVariableOp�
3_dense64/MatMulMatMul2_dense32/Relu:activations:0'3_dense64/MatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������@2
3_dense64/MatMul�
 3_dense64/BiasAdd/ReadVariableOpReadVariableOp'dense64_biasadd_readvariableop_resource*
_output_shapes
:@*
dtype02"
 3_dense64/BiasAdd/ReadVariableOp�
3_dense64/BiasAddBiasAdd3_dense64/MatMul:product:0(3_dense64/BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������@2
3_dense64/BiasAddv
3_dense64/ReluRelu3_dense64/BiasAdd:output:0*
T0*'
_output_shapes
:���������@2
3_dense64/Relu�
4_dense32/MatMul/ReadVariableOpReadVariableOp(dense32_matmul_readvariableop_resource_0*
_output_shapes

:@ *
dtype02!
4_dense32/MatMul/ReadVariableOp�
4_dense32/MatMulMatMul3_dense64/Relu:activations:0'4_dense32/MatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:��������� 2
4_dense32/MatMul�
 4_dense32/BiasAdd/ReadVariableOpReadVariableOp)dense32_biasadd_readvariableop_resource_0*
_output_shapes
: *
dtype02"
 4_dense32/BiasAdd/ReadVariableOp�
4_dense32/BiasAddBiasAdd4_dense32/MatMul:product:0(4_dense32/BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:��������� 2
4_dense32/BiasAddv
4_dense32/ReluRelu4_dense32/BiasAdd:output:0*
T0*'
_output_shapes
:��������� 2
4_dense32/Relu�
5_dense18/MatMul/ReadVariableOpReadVariableOp(dense18_matmul_readvariableop_resource_0*
_output_shapes

: *
dtype02!
5_dense18/MatMul/ReadVariableOp�
5_dense18/MatMulMatMul4_dense32/Relu:activations:0'5_dense18/MatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2
5_dense18/MatMul�
 5_dense18/BiasAdd/ReadVariableOpReadVariableOp)dense18_biasadd_readvariableop_resource_0*
_output_shapes
:*
dtype02"
 5_dense18/BiasAdd/ReadVariableOp�
5_dense18/BiasAddBiasAdd5_dense18/MatMul:product:0(5_dense18/BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2
5_dense18/BiasAddv
5_dense18/ReluRelu5_dense18/BiasAdd:output:0*
T0*'
_output_shapes
:���������2
5_dense18/Relu�
6_dense9/MatMul/ReadVariableOpReadVariableOp%dense9_matmul_readvariableop_resource*
_output_shapes

:	*
dtype02 
6_dense9/MatMul/ReadVariableOp�
6_dense9/MatMulMatMul5_dense18/Relu:activations:0&6_dense9/MatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������	2
6_dense9/MatMul�
6_dense9/BiasAdd/ReadVariableOpReadVariableOp&dense9_biasadd_readvariableop_resource*
_output_shapes
:	*
dtype02!
6_dense9/BiasAdd/ReadVariableOp�
6_dense9/BiasAddBiasAdd6_dense9/MatMul:product:0'6_dense9/BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������	2
6_dense9/BiasAdds
6_dense9/ReluRelu6_dense9/BiasAdd:output:0*
T0*'
_output_shapes
:���������	2
6_dense9/Relu�
$output_mem_clf/MatMul/ReadVariableOpReadVariableOp-output_mem_clf_matmul_readvariableop_resource*
_output_shapes

:	*
dtype02&
$output_mem_clf/MatMul/ReadVariableOp�
output_mem_clf/MatMulMatMul6_dense9/Relu:activations:0,output_mem_clf/MatMul/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2
output_mem_clf/MatMul�
%output_mem_clf/BiasAdd/ReadVariableOpReadVariableOp.output_mem_clf_biasadd_readvariableop_resource*
_output_shapes
:*
dtype02'
%output_mem_clf/BiasAdd/ReadVariableOp�
output_mem_clf/BiasAddBiasAddoutput_mem_clf/MatMul:product:0-output_mem_clf/BiasAdd/ReadVariableOp:value:0*
T0*'
_output_shapes
:���������2
output_mem_clf/BiasAdd�
output_mem_clf/SoftmaxSoftmaxoutput_mem_clf/BiasAdd:output:0*
T0*'
_output_shapes
:���������2
output_mem_clf/Softmax{
IdentityIdentity output_mem_clf/Softmax:softmax:0^NoOp*
T0*'
_output_shapes
:���������2

Identity�
NoOpNoOp!^1_dense18/BiasAdd/ReadVariableOp ^1_dense18/MatMul/ReadVariableOp!^2_dense32/BiasAdd/ReadVariableOp ^2_dense32/MatMul/ReadVariableOp!^3_dense64/BiasAdd/ReadVariableOp ^3_dense64/MatMul/ReadVariableOp!^4_dense32/BiasAdd/ReadVariableOp ^4_dense32/MatMul/ReadVariableOp!^5_dense18/BiasAdd/ReadVariableOp ^5_dense18/MatMul/ReadVariableOp ^6_dense9/BiasAdd/ReadVariableOp^6_dense9/MatMul/ReadVariableOp&^output_mem_clf/BiasAdd/ReadVariableOp%^output_mem_clf/MatMul/ReadVariableOp*"
_acd_function_control_output(*
_output_shapes
 2
NoOp"
identityIdentity:output:0*(
_construction_contextkEagerRuntime*B
_input_shapes1
/:���������	: : : : : : : : : : : : : : 2D
 1_dense18/BiasAdd/ReadVariableOp 1_dense18/BiasAdd/ReadVariableOp2B
1_dense18/MatMul/ReadVariableOp1_dense18/MatMul/ReadVariableOp2D
 2_dense32/BiasAdd/ReadVariableOp 2_dense32/BiasAdd/ReadVariableOp2B
2_dense32/MatMul/ReadVariableOp2_dense32/MatMul/ReadVariableOp2D
 3_dense64/BiasAdd/ReadVariableOp 3_dense64/BiasAdd/ReadVariableOp2B
3_dense64/MatMul/ReadVariableOp3_dense64/MatMul/ReadVariableOp2D
 4_dense32/BiasAdd/ReadVariableOp 4_dense32/BiasAdd/ReadVariableOp2B
4_dense32/MatMul/ReadVariableOp4_dense32/MatMul/ReadVariableOp2D
 5_dense18/BiasAdd/ReadVariableOp 5_dense18/BiasAdd/ReadVariableOp2B
5_dense18/MatMul/ReadVariableOp5_dense18/MatMul/ReadVariableOp2B
6_dense9/BiasAdd/ReadVariableOp6_dense9/BiasAdd/ReadVariableOp2@
6_dense9/MatMul/ReadVariableOp6_dense9/MatMul/ReadVariableOp2N
%output_mem_clf/BiasAdd/ReadVariableOp%output_mem_clf/BiasAdd/ReadVariableOp2L
$output_mem_clf/MatMul/ReadVariableOp$output_mem_clf/MatMul/ReadVariableOp:O K
'
_output_shapes
:���������	
 
_user_specified_nameinputs"�L
saver_filename:0StatefulPartitionedCall_1:0StatefulPartitionedCall_28"
saved_model_main_op

NoOp*>
__saved_model_init_op%#
__saved_model_init_op

NoOp*�
serving_default�
=
hst_jobs1
serving_default_hst_jobs:0���������	B
output_mem_clf0
StatefulPartitionedCall:0���������tensorflow/serving/predict:��
�
layer-0
layer_with_weights-0
layer-1
layer_with_weights-1
layer-2
layer_with_weights-2
layer-3
layer_with_weights-3
layer-4
layer_with_weights-4
layer-5
layer_with_weights-5
layer-6
layer_with_weights-6
layer-7
		optimizer

trainable_variables
regularization_losses
	variables
	keras_api

signatures
+�&call_and_return_all_conditional_losses
�__call__
�_default_save_signature"
_tf_keras_network
"
_tf_keras_input_layer
�

kernel
bias
trainable_variables
regularization_losses
	variables
	keras_api
+�&call_and_return_all_conditional_losses
�__call__"
_tf_keras_layer
�

kernel
bias
trainable_variables
regularization_losses
	variables
	keras_api
+�&call_and_return_all_conditional_losses
�__call__"
_tf_keras_layer
�

kernel
bias
trainable_variables
regularization_losses
	variables
 	keras_api
+�&call_and_return_all_conditional_losses
�__call__"
_tf_keras_layer
�

!kernel
"bias
#trainable_variables
$regularization_losses
%	variables
&	keras_api
+�&call_and_return_all_conditional_losses
�__call__"
_tf_keras_layer
�

'kernel
(bias
)trainable_variables
*regularization_losses
+	variables
,	keras_api
+�&call_and_return_all_conditional_losses
�__call__"
_tf_keras_layer
�

-kernel
.bias
/trainable_variables
0regularization_losses
1	variables
2	keras_api
+�&call_and_return_all_conditional_losses
�__call__"
_tf_keras_layer
�

3kernel
4bias
5trainable_variables
6regularization_losses
7	variables
8	keras_api
+�&call_and_return_all_conditional_losses
�__call__"
_tf_keras_layer
�
9iter

:beta_1

;beta_2
	<decay
=learning_ratemqmrmsmtmumv!mw"mx'my(mz-m{.m|3m}4m~vv�v�v�v�v�!v�"v�'v�(v�-v�.v�3v�4v�"
	optimizer
�
0
1
2
3
4
5
!6
"7
'8
(9
-10
.11
312
413"
trackable_list_wrapper
 "
trackable_list_wrapper
�
0
1
2
3
4
5
!6
"7
'8
(9
-10
.11
312
413"
trackable_list_wrapper
�

trainable_variables
>non_trainable_variables
?layer_metrics
@metrics
regularization_losses

Alayers
	variables
Blayer_regularization_losses
�__call__
�_default_save_signature
+�&call_and_return_all_conditional_losses
'�"call_and_return_conditional_losses"
_generic_user_object
-
�serving_default"
signature_map
": 	21_dense18/kernel
:21_dense18/bias
.
0
1"
trackable_list_wrapper
 "
trackable_list_wrapper
.
0
1"
trackable_list_wrapper
�
trainable_variables
Cnon_trainable_variables
Dlayer_metrics
Emetrics
regularization_losses

Flayers
	variables
Glayer_regularization_losses
�__call__
+�&call_and_return_all_conditional_losses
'�"call_and_return_conditional_losses"
_generic_user_object
":  22_dense32/kernel
: 22_dense32/bias
.
0
1"
trackable_list_wrapper
 "
trackable_list_wrapper
.
0
1"
trackable_list_wrapper
�
trainable_variables
Hnon_trainable_variables
Ilayer_metrics
Jmetrics
regularization_losses

Klayers
	variables
Llayer_regularization_losses
�__call__
+�&call_and_return_all_conditional_losses
'�"call_and_return_conditional_losses"
_generic_user_object
":  @23_dense64/kernel
:@23_dense64/bias
.
0
1"
trackable_list_wrapper
 "
trackable_list_wrapper
.
0
1"
trackable_list_wrapper
�
trainable_variables
Mnon_trainable_variables
Nlayer_metrics
Ometrics
regularization_losses

Players
	variables
Qlayer_regularization_losses
�__call__
+�&call_and_return_all_conditional_losses
'�"call_and_return_conditional_losses"
_generic_user_object
": @ 24_dense32/kernel
: 24_dense32/bias
.
!0
"1"
trackable_list_wrapper
 "
trackable_list_wrapper
.
!0
"1"
trackable_list_wrapper
�
#trainable_variables
Rnon_trainable_variables
Slayer_metrics
Tmetrics
$regularization_losses

Ulayers
%	variables
Vlayer_regularization_losses
�__call__
+�&call_and_return_all_conditional_losses
'�"call_and_return_conditional_losses"
_generic_user_object
":  25_dense18/kernel
:25_dense18/bias
.
'0
(1"
trackable_list_wrapper
 "
trackable_list_wrapper
.
'0
(1"
trackable_list_wrapper
�
)trainable_variables
Wnon_trainable_variables
Xlayer_metrics
Ymetrics
*regularization_losses

Zlayers
+	variables
[layer_regularization_losses
�__call__
+�&call_and_return_all_conditional_losses
'�"call_and_return_conditional_losses"
_generic_user_object
!:	26_dense9/kernel
:	26_dense9/bias
.
-0
.1"
trackable_list_wrapper
 "
trackable_list_wrapper
.
-0
.1"
trackable_list_wrapper
�
/trainable_variables
\non_trainable_variables
]layer_metrics
^metrics
0regularization_losses

_layers
1	variables
`layer_regularization_losses
�__call__
+�&call_and_return_all_conditional_losses
'�"call_and_return_conditional_losses"
_generic_user_object
':%	2output_mem_clf/kernel
!:2output_mem_clf/bias
.
30
41"
trackable_list_wrapper
 "
trackable_list_wrapper
.
30
41"
trackable_list_wrapper
�
5trainable_variables
anon_trainable_variables
blayer_metrics
cmetrics
6regularization_losses

dlayers
7	variables
elayer_regularization_losses
�__call__
+�&call_and_return_all_conditional_losses
'�"call_and_return_conditional_losses"
_generic_user_object
:	 (2	Adam/iter
: (2Adam/beta_1
: (2Adam/beta_2
: (2
Adam/decay
: (2Adam/learning_rate
 "
trackable_list_wrapper
 "
trackable_dict_wrapper
.
f0
g1"
trackable_list_wrapper
X
0
1
2
3
4
5
6
7"
trackable_list_wrapper
 "
trackable_list_wrapper
 "
trackable_list_wrapper
 "
trackable_dict_wrapper
 "
trackable_list_wrapper
 "
trackable_list_wrapper
 "
trackable_list_wrapper
 "
trackable_list_wrapper
 "
trackable_dict_wrapper
 "
trackable_list_wrapper
 "
trackable_list_wrapper
 "
trackable_list_wrapper
 "
trackable_list_wrapper
 "
trackable_dict_wrapper
 "
trackable_list_wrapper
 "
trackable_list_wrapper
 "
trackable_list_wrapper
 "
trackable_list_wrapper
 "
trackable_dict_wrapper
 "
trackable_list_wrapper
 "
trackable_list_wrapper
 "
trackable_list_wrapper
 "
trackable_list_wrapper
 "
trackable_dict_wrapper
 "
trackable_list_wrapper
 "
trackable_list_wrapper
 "
trackable_list_wrapper
 "
trackable_list_wrapper
 "
trackable_dict_wrapper
 "
trackable_list_wrapper
 "
trackable_list_wrapper
 "
trackable_list_wrapper
 "
trackable_list_wrapper
 "
trackable_dict_wrapper
 "
trackable_list_wrapper
 "
trackable_list_wrapper
 "
trackable_list_wrapper
N
	htotal
	icount
j	variables
k	keras_api"
_tf_keras_metric
^
	ltotal
	mcount
n
_fn_kwargs
o	variables
p	keras_api"
_tf_keras_metric
:  (2total
:  (2count
.
h0
i1"
trackable_list_wrapper
-
j	variables"
_generic_user_object
:  (2total
:  (2count
 "
trackable_dict_wrapper
.
l0
m1"
trackable_list_wrapper
-
o	variables"
_generic_user_object
':%	2Adam/1_dense18/kernel/m
!:2Adam/1_dense18/bias/m
':% 2Adam/2_dense32/kernel/m
!: 2Adam/2_dense32/bias/m
':% @2Adam/3_dense64/kernel/m
!:@2Adam/3_dense64/bias/m
':%@ 2Adam/4_dense32/kernel/m
!: 2Adam/4_dense32/bias/m
':% 2Adam/5_dense18/kernel/m
!:2Adam/5_dense18/bias/m
&:$	2Adam/6_dense9/kernel/m
 :	2Adam/6_dense9/bias/m
,:*	2Adam/output_mem_clf/kernel/m
&:$2Adam/output_mem_clf/bias/m
':%	2Adam/1_dense18/kernel/v
!:2Adam/1_dense18/bias/v
':% 2Adam/2_dense32/kernel/v
!: 2Adam/2_dense32/bias/v
':% @2Adam/3_dense64/kernel/v
!:@2Adam/3_dense64/bias/v
':%@ 2Adam/4_dense32/kernel/v
!: 2Adam/4_dense32/bias/v
':% 2Adam/5_dense18/kernel/v
!:2Adam/5_dense18/bias/v
&:$	2Adam/6_dense9/kernel/v
 :	2Adam/6_dense9/bias/v
,:*	2Adam/output_mem_clf/kernel/v
&:$2Adam/output_mem_clf/bias/v
�2�
M__inference_memory_classifier_layer_call_and_return_conditional_losses_925857
M__inference_memory_classifier_layer_call_and_return_conditional_losses_925910
M__inference_memory_classifier_layer_call_and_return_conditional_losses_925724
M__inference_memory_classifier_layer_call_and_return_conditional_losses_925763�
���
FullArgSpec1
args)�&
jself
jinputs

jtraining
jmask
varargs
 
varkw
 
defaults�
p 

 

kwonlyargs� 
kwonlydefaults� 
annotations� *
 
�2�
2__inference_memory_classifier_layer_call_fn_925477
2__inference_memory_classifier_layer_call_fn_925943
2__inference_memory_classifier_layer_call_fn_925976
2__inference_memory_classifier_layer_call_fn_925685�
���
FullArgSpec1
args)�&
jself
jinputs

jtraining
jmask
varargs
 
varkw
 
defaults�
p 

 

kwonlyargs� 
kwonlydefaults� 
annotations� *
 
�B�
!__inference__wrapped_model_925319hst_jobs"�
���
FullArgSpec
args� 
varargsjargs
varkwjkwargs
defaults
 

kwonlyargs� 
kwonlydefaults
 
annotations� *
 
�2�
E__inference_1_dense18_layer_call_and_return_conditional_losses_925987�
���
FullArgSpec
args�
jself
jinputs
varargs
 
varkw
 
defaults
 

kwonlyargs� 
kwonlydefaults
 
annotations� *
 
�2�
*__inference_1_dense18_layer_call_fn_925996�
���
FullArgSpec
args�
jself
jinputs
varargs
 
varkw
 
defaults
 

kwonlyargs� 
kwonlydefaults
 
annotations� *
 
�2�
E__inference_2_dense32_layer_call_and_return_conditional_losses_926007�
���
FullArgSpec
args�
jself
jinputs
varargs
 
varkw
 
defaults
 

kwonlyargs� 
kwonlydefaults
 
annotations� *
 
�2�
*__inference_2_dense32_layer_call_fn_926016�
���
FullArgSpec
args�
jself
jinputs
varargs
 
varkw
 
defaults
 

kwonlyargs� 
kwonlydefaults
 
annotations� *
 
�2�
E__inference_3_dense64_layer_call_and_return_conditional_losses_926027�
���
FullArgSpec
args�
jself
jinputs
varargs
 
varkw
 
defaults
 

kwonlyargs� 
kwonlydefaults
 
annotations� *
 
�2�
*__inference_3_dense64_layer_call_fn_926036�
���
FullArgSpec
args�
jself
jinputs
varargs
 
varkw
 
defaults
 

kwonlyargs� 
kwonlydefaults
 
annotations� *
 
�2�
E__inference_4_dense32_layer_call_and_return_conditional_losses_926047�
���
FullArgSpec
args�
jself
jinputs
varargs
 
varkw
 
defaults
 

kwonlyargs� 
kwonlydefaults
 
annotations� *
 
�2�
*__inference_4_dense32_layer_call_fn_926056�
���
FullArgSpec
args�
jself
jinputs
varargs
 
varkw
 
defaults
 

kwonlyargs� 
kwonlydefaults
 
annotations� *
 
�2�
E__inference_5_dense18_layer_call_and_return_conditional_losses_926067�
���
FullArgSpec
args�
jself
jinputs
varargs
 
varkw
 
defaults
 

kwonlyargs� 
kwonlydefaults
 
annotations� *
 
�2�
*__inference_5_dense18_layer_call_fn_926076�
���
FullArgSpec
args�
jself
jinputs
varargs
 
varkw
 
defaults
 

kwonlyargs� 
kwonlydefaults
 
annotations� *
 
�2�
D__inference_6_dense9_layer_call_and_return_conditional_losses_926087�
���
FullArgSpec
args�
jself
jinputs
varargs
 
varkw
 
defaults
 

kwonlyargs� 
kwonlydefaults
 
annotations� *
 
�2�
)__inference_6_dense9_layer_call_fn_926096�
���
FullArgSpec
args�
jself
jinputs
varargs
 
varkw
 
defaults
 

kwonlyargs� 
kwonlydefaults
 
annotations� *
 
�2�
J__inference_output_mem_clf_layer_call_and_return_conditional_losses_926107�
���
FullArgSpec
args�
jself
jinputs
varargs
 
varkw
 
defaults
 

kwonlyargs� 
kwonlydefaults
 
annotations� *
 
�2�
/__inference_output_mem_clf_layer_call_fn_926116�
���
FullArgSpec
args�
jself
jinputs
varargs
 
varkw
 
defaults
 

kwonlyargs� 
kwonlydefaults
 
annotations� *
 
�B�
$__inference_signature_wrapper_925804hst_jobs"�
���
FullArgSpec
args� 
varargs
 
varkwjkwargs
defaults
 

kwonlyargs� 
kwonlydefaults
 
annotations� *
 �
E__inference_1_dense18_layer_call_and_return_conditional_losses_925987\/�,
%�"
 �
inputs���������	
� "%�"
�
0���������
� }
*__inference_1_dense18_layer_call_fn_925996O/�,
%�"
 �
inputs���������	
� "�����������
E__inference_2_dense32_layer_call_and_return_conditional_losses_926007\/�,
%�"
 �
inputs���������
� "%�"
�
0��������� 
� }
*__inference_2_dense32_layer_call_fn_926016O/�,
%�"
 �
inputs���������
� "���������� �
E__inference_3_dense64_layer_call_and_return_conditional_losses_926027\/�,
%�"
 �
inputs��������� 
� "%�"
�
0���������@
� }
*__inference_3_dense64_layer_call_fn_926036O/�,
%�"
 �
inputs��������� 
� "����������@�
E__inference_4_dense32_layer_call_and_return_conditional_losses_926047\!"/�,
%�"
 �
inputs���������@
� "%�"
�
0��������� 
� }
*__inference_4_dense32_layer_call_fn_926056O!"/�,
%�"
 �
inputs���������@
� "���������� �
E__inference_5_dense18_layer_call_and_return_conditional_losses_926067\'(/�,
%�"
 �
inputs��������� 
� "%�"
�
0���������
� }
*__inference_5_dense18_layer_call_fn_926076O'(/�,
%�"
 �
inputs��������� 
� "�����������
D__inference_6_dense9_layer_call_and_return_conditional_losses_926087\-./�,
%�"
 �
inputs���������
� "%�"
�
0���������	
� |
)__inference_6_dense9_layer_call_fn_926096O-./�,
%�"
 �
inputs���������
� "����������	�
!__inference__wrapped_model_925319�!"'(-.341�.
'�$
"�
hst_jobs���������	
� "?�<
:
output_mem_clf(�%
output_mem_clf����������
M__inference_memory_classifier_layer_call_and_return_conditional_losses_925724r!"'(-.349�6
/�,
"�
hst_jobs���������	
p 

 
� "%�"
�
0���������
� �
M__inference_memory_classifier_layer_call_and_return_conditional_losses_925763r!"'(-.349�6
/�,
"�
hst_jobs���������	
p

 
� "%�"
�
0���������
� �
M__inference_memory_classifier_layer_call_and_return_conditional_losses_925857p!"'(-.347�4
-�*
 �
inputs���������	
p 

 
� "%�"
�
0���������
� �
M__inference_memory_classifier_layer_call_and_return_conditional_losses_925910p!"'(-.347�4
-�*
 �
inputs���������	
p

 
� "%�"
�
0���������
� �
2__inference_memory_classifier_layer_call_fn_925477e!"'(-.349�6
/�,
"�
hst_jobs���������	
p 

 
� "�����������
2__inference_memory_classifier_layer_call_fn_925685e!"'(-.349�6
/�,
"�
hst_jobs���������	
p

 
� "�����������
2__inference_memory_classifier_layer_call_fn_925943c!"'(-.347�4
-�*
 �
inputs���������	
p 

 
� "�����������
2__inference_memory_classifier_layer_call_fn_925976c!"'(-.347�4
-�*
 �
inputs���������	
p

 
� "�����������
J__inference_output_mem_clf_layer_call_and_return_conditional_losses_926107\34/�,
%�"
 �
inputs���������	
� "%�"
�
0���������
� �
/__inference_output_mem_clf_layer_call_fn_926116O34/�,
%�"
 �
inputs���������	
� "�����������
$__inference_signature_wrapper_925804�!"'(-.34=�:
� 
3�0
.
hst_jobs"�
hst_jobs���������	"?�<
:
output_mem_clf(�%
output_mem_clf���������