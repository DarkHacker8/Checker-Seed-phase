How does it work?

Uploading seed phrases and proxies:
The program reads a list of seed phrases from a file seeds.txt (each phrase is a separate line).

Proxy servers are loaded from a file proxies.txt (format: ip:port:login:password).

Address generation:
Up to 20 Ethereum addresses are generated for each seed phrase according to the BIP44 standard.

Balance check:
For each address, a request is sent to the Blockscan public API via a random proxy.

If the address has a balance, the result is written to a file. result.txt .

Asynchronous processing:
Asynchrony (asyncio, aiohttp) is used to check a large number of addresses simultaneously.

The maximum number of simultaneous requests is set by the MAX_CONCURRENT_REQUESTS parameter.

Error logging:
All errors are recorded in the errors.log file.

What can the program do?

Generate Ethereum addresses from seed phrases.

Massively check balances at these addresses via the public API.

Use a proxy to bypass IP restrictions and anonymity.

Automatically save the results (wallets with balance) and errors in separate files.

Work asynchronously and efficiently process large amounts of data.

Important!

The program does not hack wallets or select seed phrases, but only checks existing ones.

It is illegal to use someone else's seed phrases without permission.

The script can be useful for auditing your own wallets or analyzing leaks, but not for illegal actions.
