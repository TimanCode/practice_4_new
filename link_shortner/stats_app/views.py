from django.shortcuts import render
from django.http import JsonResponse
import socket
import json


class TCPClient:
    BUFFER_SIZE = 4096*2
    IP = '127.0.0.1'
    PORT = 6379
    filepath = 'stats.data'
    def createConnection(self):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (self.IP, self.PORT)
        client_socket.connect(server_address)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.BUFFER_SIZE)
        return client_socket

    def sendTCP(self, filepath, query):
        client_socket = self.createConnection()
        path_length = len(filepath).to_bytes(4, 'little')
        client_socket.send(path_length)
        path_length = len(query).to_bytes(4, 'little')
        client_socket.send(path_length)
        client_socket.send(filepath.encode())
        client_socket.send(query.encode())
        return client_socket

    def sendHT(self, name, key, value):
        query = "HSET " + name + " " + str(value) + " " + str(key) + '\0'
        client_socket = self.sendTCP(self.filepath, query)
        client_socket.close()

    def recvHT(self, name, value):
        query = "HGET " + name + " " + str(value) + '\0'
        client_socket = self.sendTCP(self.filepath, query)

        received_data = b''
        received_data = client_socket.recv(4)
        len = ord(received_data.decode("latin-1")[0])
        received_data = client_socket.recv(len*1000)


        received_data = received_data.decode("latin-1")
        client_socket.close()
        return received_data

    def delHT(self, name, key):
        query = "HDEL " + name + " " + str(key) + '\0'
        client_socket = self.sendTCP(self.filepath, query)
        client_socket.close()

    def recvQ(self, name):
        query = "QPOP " + name + '\0'
        s = ""
        for i in range(3):
            client_socket = self.sendTCP(self.filepath, query)

            received_data = b''
            received_data = client_socket.recv(4)
            len = ord(received_data.decode("latin-1")[0])
            received_data = client_socket.recv(len * 1000)

            received_data = received_data.decode("latin-1")
            s+= received_data + ", "
            client_socket.close()
        return s

class report:
    report_logs = []
    ht_name = "logs"
    k = "key"

    def add(self, log):
        self.report_logs.append(log)
        self.update()

    def urlInReport(self, url):
        for i in range(len(self.report_logs)):
            if self.report_logs[i]['URL'] == url:
                return i
        return -1

    def create(self):
        newTCP = TCPClient()
        newTCP.sendHT(self.ht_name, json.dumps(self.report_logs), "key")

    def get(self):
        newTCP = TCPClient()
        temp = newTCP.recvHT(self.ht_name, self.k)
        if "No key" not in temp:
            self.report_logs = json.loads(temp)

    def checkUpdates(self):
        newTCP = TCPClient()
        while(True):
            temp = newTCP.recvQ("new")
            if "is empty" in temp:
                print("\tNo new logs")
                break
            print("\t", temp)
            new_log = json.loads(temp[:len(temp)-2])
            self.add(new_log)
        self.update()

    def update(self):
        newTCP = TCPClient()
        newTCP.delHT(self.ht_name, self.k)
        self.create()

    def getCount(self, v, f):
        c = 0
        for i in self.report_logs:
            if i[f] == v:
                c += 1
        return c

    def createReport(self, dimension):
        report_data = []
        uniq = set()

        for i in self.report_logs:
            uniq.add(i[dimension[0]])

        for i in uniq:
            log = {
                dimension[0]: i,
                "Count1": 0,
                dimension[1]: None,
                "Count2": [],
                dimension[2]: None,
                "Count3": [],
            }
            log['Count1'] = self.getCount(i, dimension[0])
            report_data.append(log)

            uniq1 = set()
            uniq2 = set()

            for j in self.report_logs:
                if j[dimension[0]] == i:
                    uniq1.add(j[dimension[1]])
                    uniq2.add(j[dimension[2]])
            for j in uniq1:
                c = 0
                for t in self.report_logs:
                    if t[dimension[0]] == i:
                        if t[dimension[1]] == j:
                            c += 1
                log['Count2'].append(c)
            for j in uniq2:
                c = 0
                for t in self.report_logs:
                    if t[dimension[0]] == i:
                        if t[dimension[2]] == j:
                            c += 1
                log['Count3'].append(c)

            t1 = list(uniq1)
            log[dimension[1]] = t1
            t1 = list(uniq2)
            log[dimension[2]] = t1
        json_report = json.dumps(report_data, indent=4)

        html = ''
        for i in report_data:
            html += f"<pre>{i[dimension[0]]} ({i['Count1']}) \n"
            for j in range(len(i[dimension[1]])):
                html += f"\t {i[dimension[1]][j]} ({i['Count2'][j]})\n"
                for k in range(len(i[dimension[2]])):
                    html += f"\t\t {i[dimension[2]][k]}\n"
            html += "</pre>"
        return html


def report_stats(request):
    reports = report()
    reports.get()
    reports.checkUpdates()
    dimension = {
        "Dimensions": ["TimeInterval", "URL", "SourceIP"]
    }
    return render(request, 'report/report.html', {'items': reports.createReport(dimension['Dimensions'])})
    #return JsonResponse(json.loads(reports.createReport(dimension['Dimensions'])), safe=False)


