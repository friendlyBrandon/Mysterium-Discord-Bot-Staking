   #!/bin/bash

# Configuration
RPC_URL="https://polygon-rpc.com/"
WALLET_ADDRESS="YOUROWNWALLETADDRESS"
MYST_CONTRACT="0x1379E8886A944d2D9d440b3d88DF536Aea08d9F3"
NFT_CONTRACT="YOUROWN_NFT_CONTRACT"
STAKING_CONTRACT="0xbf9f6b1d910aa207daa400931430ef110570f8ff"
TOKEN_ID="2109450184878881661802354601412081741494792450863972690982614294921869121499"

# Function to make RPC call
make_rpc_call() {
    local data=$1
    local contract=$2
    curl -s -X POST \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","method":"eth_call","params":[{"to":"'$contract'","data":"'$>
        $RPC_URL | grep -o '"result":"0x[0-9a-f]*"' | cut -d'"' -f4
}

# Function to get token balance
   get_balance() {
    local data="0x70a08231000000000000000000000000${WALLET_ADDRESS#0x}"
    local result=$(make_rpc_call "$data" "$MYST_CONTRACT")
    if [ -n "$result" ] && [ "$result" != "0x" ]; then
        local decimal=$(echo "ibase=16; $(echo ${result#0x} | tr '[:lower:]' '[:upper:]')" | bc 2>/dev/null)
        echo "scale=18; $decimal / 10^18" | bc -l
    else
        echo "0"
    fi
}

# Function to convert decimal to 64-character hex
decimal_to_hex64() {
    local decimal=$1
    # Convert decimal to hex using bc
    local hex=$(echo "obase=16; $decimal" | bc | tr -d '\\' | tr -d '\n' | tr '[:upper:]' '[:lower:]')
    # Pad with leading zeros to 64 characters
    printf "%064s" "$hex" | tr ' ' '0'
}

# Function to get staked amount
get_staked() {
    local token_hex=$(decimal_to_hex64 "$TOKEN_ID")
    local data="0xce325bf8$token_hex"
    local result=$(make_rpc_call "$data" "$STAKING_CONTRACT")
    if [ -n "$result" ] && [ "$result" != "0x" ]; then
        local value_hex="0x${result:2:64}"
        local decimal=$(echo "ibase=16; $(echo ${value_hex#0x} | tr '[:lower:]' '[:upper:]')" | bc 2>/dev/null)
        echo "scale=18; $decimal / 10^18" | bc -l
    else
        echo "0"
    fi
}

# Function to get pending rewards
get_rewards() {
    local token_hex=$(decimal_to_hex64 "$TOKEN_ID")
    local data="0xabfe35ad$token_hex"
    local result=$(make_rpc_call "$data" "$STAKING_CONTRACT")
    if [ -n "$result" ] && [ "$result" != "0x" ]; then
        local decimal=$(echo "ibase=16; $(echo ${result#0x} | tr '[:lower:]' '[:upper:]')" | bc 2>/dev/null)
        echo "scale=18; $decimal / 10^18" | bc -l
    else
        echo "0"
    fi
}

# Main metrics function
serve_metrics() {
    local balance=$(get_balance)
    local staked=$(get_staked)
    local rewards=$(get_rewards)
    
    cat << EOF
# HELP myst_balance MYST token balance
# TYPE myst_balance gauge
myst_balance $balance
# HELP myst_staked_amount Staked MYST amount
# TYPE myst_staked_amount gauge
myst_staked_amount $staked
# HELP myst_pending_rewards Pending staking rewards in MYST
# TYPE myst_pending_rewards gauge
myst_pending_rewards $rewards
EOF
}

# Run as a web server
echo "Starting metrics server on port 8000"
while true; do
    echo -e "HTTP/1.1 200 OK\nContent-Type: text/plain; version=0.0.4\n\n$(serve_metrics)" | nc -l -p 8000 -q 1
done