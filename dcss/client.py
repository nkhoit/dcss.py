import crawlConnection as cc

def getRemoteConnection(username, password):
	result = cc.RemoteCC(username, password)
	if(result.connect):
		result.login()
	else:
		print("Failed to connect to cao. Are you sure the server is up?")
		result = None
	return result