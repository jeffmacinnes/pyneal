function response = getFromPyneal(host, port, volIdx)
% getFromPyneal(host, port, volIdx)
% JJM - 2021/01/07  
% 
% Send request to Pyneal for analysis results from a specific volume 
%
% Inputs -
%   host:   IP address of machine running Pyneal
%   port:   port number that Pyneal is listening for requests on
%   volIdx: volume index that you are requesting results from.
%           Note, volume index uses 0-based index (e.g. first volume: 0)
%
% Outputs -
%   response:   structure var representing parsed JSON results returned from
%               Pyneal.
% 
% Example usage: 
%   response = getFromPyneal('10.0.0.1', 5556, 99);
%
% Sample JSON returned from Pyneal: '{"Average": 2458, "foundResults": true}'
%
% This would be parsed as: 
%   response = 
%           struct with fields:
%               Average: 2458
%               foundResults: 1
%               connStatus: 1
%
% NOTE: THIS TOOL REQUIRES JSONLab 1.9 library
%       https://github.com/fangq/jsonlab

timeout = 5;
requestedVol = num2str(volIdx, '%04i');    % format volIdx as 4-char string

try
    % open socket, send request
    sock = tcpip(host, port, 'Timeout', timeout);
    fopen(sock);
    fprintf(sock, requestedVol);

    % listen for response
    message = fgetl(sock);           % read full message (terminates with newline)
    fclose(sock);

    % parse JSON message
    response = loadjson(message);
    response.connStatus = 1;
catch e
    % if socket fails, return structure with status code set to 0
    response = struct('connStatus', 0);
    
    % but print the error
    fprintf('ERROR:\n \thost: %s\n \tport: %d\n \trequest: %s\n', host, port, requestedVol);
    disp(e);
end


