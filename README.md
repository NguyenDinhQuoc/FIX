# FIX Client

## Setup
Use conda to create a virtual environment
```sh
conda create -n auto_trader python=3.7
```
```sh
conda activate auto_trader
```

Once inside the virtual environment, go to the project folder for this client and install all dependencies:

```sh
pip install -r requirements.txt
```

## How to Use

An example run can be done with the following command:

```sh
python main.py --config <config_file_name>
```

The *config_file_name* is the path to the config file  

Example Run

```sh
python main.py --config configs/fix/DTL.cfg
```
From the CLI one can perform actions such as selling, buying. An action must be followed by 'tags' from the FIX protocol. Each is tag preceeded with a hyphen '-' and followed by its corresponding value. For example:

```
"  -54 1 -55 MSFT -40 1  -38 10"
```

The example above indicates a buy order (NewOrderSingle) for the symbol 'MSFT' at a market price and an order size of 10.

## Document
The function 'resetSeqLogOn' set the ResetSeqNumFlag to True, so that the sequence number will reset when logon
Each time I sent a message, I call '_make_standard_header' function to create a standard hearder. This function also increase sequence number.

To send a new order, call function 'OneOrder'
for example
```
    _, options = parse_fix_options("  -54 1 -55 MSFT -40 1 -44 1.145 -38 100000")
    app.app.buy(**options)
```
This will send a purchase order to the server and we will receive an execution report (35=8) with information about the trade.
To Cancel a request, call function 'cancel_order'
for example
```
    _, options = parse_fix_options(" -54 1 -55 MSFT -40 2 -38 10 167 NONE")
    app.app.cancel_order(**options)
```
For reject (35=3), execution report (35=8), Order Cancel Reject (35=9) there is a function 'print_report' at 'fromAdmin' which handle in such cases.

File main.py send 1000 random orders (requirement 9^th) and randomly cancel it.

