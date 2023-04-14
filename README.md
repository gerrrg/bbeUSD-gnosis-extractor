Recommend using Python 3.9.  You can install it on a mac with homebrew `brew install python@3.9`

You will also need ganahce-cli installed.  `npm install ganache-cli`

Install dependancies.  You can setup a venv if you want
```bash
python3.9 -m venv venv
source venv/bin/activate
pip3.9 install requirements.txt
```
Edit the script in [scripts/extractInFork.py](scripts/extractInFork.py) and change the address of multisig to your address.  It doesn't have to be a multisig to run the simulation, but you can only load the resulting payload into a gnosis safe.

Check all the other addresses and make sure they make sense/you understand.

Review the script breifly and make sure that no other addresses are used and you understand to at least this level.

Run the script from the scripts directory
```bash
cd scripts
brownie run --network mainnet-fork scripts/extractInFork.py
```

It should print a bunch of stuff, and at the end a report that looks something lke this:
```text
*** Final report.
BPTS burnt: 375523826997996321598041
USDC in:61995.513759
USDT in:4.080702
DAI in: 64590.65470597399
```

A file will be created called EulerBreakoutOutput.json.  If the address provided as multisig was a multisig, you can load this into transaction builder and simulate the results on tenderly.  Once loaded into the safe, the transaction is reasonably easy to read.