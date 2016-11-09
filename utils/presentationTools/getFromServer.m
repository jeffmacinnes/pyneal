function reply = getFromServer(host, port, volume)

% function to request a specific volume's output from the real-time server
% returns a string
% uses the java socket library
% usage: 
%       reply = getFromServer(host, port, volume)

import java.net.*
import java.io.*

max_attempts = 10;
attempt = 0;
while true
    if attempt == max_attempts
        disp(['too many attempts to get volume ' num2str(volume)]);
        break
    end 
    attempt = attempt + 1;
    try 
        % attempt to establish the socket, will throw if not
        sock = Socket(host, port);
        
        % establish input stream
        in = BufferedReader(InputStreamReader(sock.getInputStream));

        % establish output stream
        out = PrintWriter(sock.getOutputStream, true);

        % make request
        out.println(num2str(volume))

        % wait for reply
        reply = in.readLine();

        % close the socket
        sock.close()        
        break;
    catch
        pause(.1)
    end
end




