Create your own bot on Discord, add it to your own server and give it admin permission.
Get the token to put on line 12 inbetween the ''.
Also change the CHANNEL_ID to your own channel its ID.

Now for StakingMonitor.sh:
Edit the following:

- WALLET_ADDRESS="YOUROWNWALLETADDRESS" (line 5, change it to your own polygon network address.)
- NFT_CONTRACT="YOUROWN_NFT_CONTRACT" (line 7, change with your own NFT contract found when your first staked, go into the transaction on polygonscan and then state of the transaction. Once you're there you should be able to find sMYST, the address where its sent from is the contract.)

Please use some kind of background task manager (such as screen or tmux to manage these scripts)

Please edit the following in main.py on line 12 and 13:

- TOKEN = 'YOUR_BOT_TOKEN' # Replace with your own bot its token, also give the bot admin perms
- CHANNEL_ID = 123456789  # Replace with the actual channel ID

The following commands you need to run the StakingMonitor.sh:
- chmod +x StakingMonitor.sh 
- ./StakingMonitor.sh

Now for the Python script:
- python3 -m venv venv
- source venv/bin/activate
- pip install discord.py aiohttp matplotlib 

Enjoy! <3