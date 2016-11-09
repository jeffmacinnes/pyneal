function drawThermometer(window, position, height, range, target_values, colors)
% - jjm 8/9/11
% thermometer visualization
% This scipt will construct a thermometer according to the input parameters provided
% NOTE: The script that calls this function must still call Screen('Flip', WinPtr) to display the thermometer 
% usage:
%   >> drawThermometer(window, position, height, range [, target_value], [colors])
%
% window: Window pointer
% position: [x,y] coordinate at which to center the thermometer
% height: height of the thermometer level (in arbitrary thermometer units)
% range: [min, max] range of the thermometer (in arbitrary thermometer units)
% [target_values]: value (in thermometer units) at which to place a line. 
%                  can be 2 values [a,b]: first will be solid line, 2nd
%                  will be dashed line
% [colors]: {[R G B], [R G B]} matlab color codes for negative and
%           positive therm values, respectively


% Thermometer Settings:
therm_box = [100, 400];          % dimensions of the thermometer
therm_box_color = 255;           % color of the thermometer border
therm_box_wt = 2;                % thickness of the thermometer border
text_color = 255;                % text color
text_size = 25;
origin = [(position(1)-(therm_box(1)/2)) (position(2)-(therm_box(2)/2))]; 

if nargin >= 5                  % if a target value has been specified, turn the includeTarget flag on
    includeTargets = ones(1,length(target_values));
else
    includeTargets = 0;
end

if nargin == 6
    neg_color = colors{1};
    pos_color = colors{2};
else
    neg_color = [96, 165, 204];      % default color for negative thermometer values (baby blue)
    pos_color = [230, 66, 59];       % default color for positive thermometer values (red)
end


% Initial Setup
Screen('TextSize', window, text_size);

% round range to nearest tenth
range = [round(range(1)*10)/10, round(range(2)*10)/10];

% Check if height exceeds range. If so, set height to match max or min
if (height < range(1))
    disp('height exceeds the range')
    height = range(1);
elseif (height > range(2))
    disp('height exceeds the range')
    height = range(2);
end

% Check if each target_value falls within the range. If not, exclude it
if sum(includeTargets) ~= 0;
    for t = 1:length(includeTargets)
        if target_values(t) < range(1) || target_values(t) > range(2)
            includeTargets(t) = 0;
        end
    end
end

% set up thermometer parameters
min_height = range(1);           % minimum value of the thermometer
max_height = range(2);           % maximum value of the thermometer
therm_range = range(2)-range(1); % range of the thermometer (in arbitrary thermometer units)

if min_height < 0
    isBidirectional = 1;            % if min is lower than zero, make the thermometer bi-directional
    zero_location = (abs(min_height)/therm_range) * therm_box(2);      % calculate the zero axis location as % of thermometer box height       
else
    isBidirectional = 0;
    zero_location = 0;
end
unit_height = therm_box(2)/therm_range;      % calculate the height, in pixels, of each arbitrary thermometer unit 

% Setup line types for each new target that is to be added (max 2, so far).
% line styles represented by 16-element logical array
line_styles = zeros(2, 16);
line_styles(1,:) = [1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1];       % solid
line_styles(2,:) = [1 1 1 1 0 0 0 0 1 1 1 1 0 0 0 0];       % dashed

% Draw Border box, add min and max text
Screen('LineStipple', window, 1, 1, line_styles(1,:));         % set the appropriate line style
Screen('FrameRect', window, therm_box_color, [origin(1), origin(2), origin(1)+therm_box(1), origin(2)+therm_box(2)], therm_box_wt);
Screen('DrawText', window, num2str(max_height), origin(1)-45, origin(2)-15, text_color);
if isBidirectional == 1
    Screen('DrawText', window, num2str(min_height), origin(1)-65, origin(2) + therm_box(2) - 15, text_color);
end

% Draw Thermometer bar
if height ~= 0
    if height == abs(height)            % check whether the height is positive or negative (relative to 0)
        isPositive = 1;
    else
        isPositive = 0;
    end
    bar_height = ceil(abs(height)*unit_height);              % calculate the height, in pixels, of the bar
    
    if isPositive == 1
        bar_x1 = origin(1) + therm_box_wt;
        bar_y1 = origin(2) + therm_box_wt + (therm_box(2) - zero_location - bar_height);
        bar_x2 = origin(1) + therm_box(1) - therm_box_wt;
        bar_y2 = origin(2) + (therm_box(2) - zero_location);
        if bar_y2 <= bar_y1
            bar_y2 = bar_y1+1;
        end
        Screen('FillRect', window, pos_color, [bar_x1, bar_y1, bar_x2, bar_y2]);

    else
        bar_x1 = origin(1) + therm_box_wt;
        bar_y1 = origin(2) + (therm_box(2) - zero_location) + 1;
        bar_x2 = origin(1) + therm_box(1) - therm_box_wt;
        bar_y2 = origin(2) + (therm_box(2) - zero_location) + bar_height - therm_box_wt;
        if bar_y2 <= bar_y1
            bar_y2 = bar_y1+1;
        end
        Screen('FillRect', window, neg_color, [bar_x1, bar_y1, bar_x2, bar_y2]);
    end
end

% Draw Zero tick mark
Screen('LineStipple', window, 1, 1, line_styles(1,:));         % set the appropriate line style
Screen('DrawLine', window, therm_box_color, origin(1)-15, origin(2)+therm_box(2)-zero_location, origin(1)+therm_box(1)+15, origin(2)+therm_box(2)-zero_location);
Screen('DrawText', window, '0', origin(1)-40, origin(2) + (therm_box(2) - zero_location) - 15, text_color);

% Draw target tickmarks (if indicated)
if sum(includeTargets) ~= 0
    for t = 1:length(includeTargets)
       if includeTargets(t) == 1                                        % for each target that is to be included
           target_y = (max_height - target_values(t)) * unit_height;    % set the appropriate position
           Screen('LineStipple', window, 1, 1, line_styles(t,:));         % set the appropriate line style
           Screen('DrawLine', window, 230, origin(1)-14, origin(2)+target_y, origin(1)+therm_box(1)+15, origin(2)+target_y, 3);
       end
    end
end




