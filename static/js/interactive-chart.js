(function(window, document) {
    'use strict';

    var SVG_NS = 'http://www.w3.org/2000/svg';
    var WIDTH = 1000;
    var HEIGHT = 500;
    var MARGIN = {left: 105, right: 35, top: 58, bottom: 70};

    function svgElement(name, attributes, parent) {
        var element = document.createElementNS(SVG_NS, name);
        Object.keys(attributes || {}).forEach(function(key) {
            element.setAttribute(key, attributes[key]);
        });
        if (parent) {
            parent.appendChild(element);
        }
        return element;
    }

    function textElement(parent, x, y, value, attributes) {
        var attrs = attributes || {};
        attrs.x = x;
        attrs.y = y;
        var element = svgElement('text', attrs, parent);
        element.textContent = value;
        return element;
    }

    function sign(value) {
        return value < 0 ? -1 : value > 0 ? 1 : 0;
    }

    function endpointSlope(h0, h1, delta0, delta1) {
        var slope = ((2 * h0 + h1) * delta0 - h0 * delta1) / (h0 + h1);
        if (sign(slope) !== sign(delta0)) {
            return 0;
        }
        if (sign(delta0) !== sign(delta1) && Math.abs(slope) > Math.abs(3 * delta0)) {
            return 3 * delta0;
        }
        return slope;
    }

    function pchipCurve(points, sampleCount) {
        var clean = points
            .map(function(point) { return {x: Number(point.x), y: Number(point.y)}; })
            .filter(function(point) { return isFinite(point.x) && isFinite(point.y); })
            .sort(function(a, b) { return a.x - b.x; });

        if (clean.length < 2) {
            return clean;
        }

        var x = clean.map(function(point) { return point.x; });
        var y = clean.map(function(point) { return point.y; });
        var h = [];
        var delta = [];
        var derivatives = new Array(clean.length);
        var i;

        for (i = 0; i < clean.length - 1; i++) {
            h.push(x[i + 1] - x[i]);
            delta.push((y[i + 1] - y[i]) / h[i]);
        }

        if (clean.length === 2) {
            derivatives[0] = delta[0];
            derivatives[1] = delta[0];
        } else {
            derivatives[0] = endpointSlope(h[0], h[1], delta[0], delta[1]);
            derivatives[clean.length - 1] = endpointSlope(
                h[h.length - 1],
                h[h.length - 2],
                delta[delta.length - 1],
                delta[delta.length - 2]
            );
            for (i = 1; i < clean.length - 1; i++) {
                if (delta[i - 1] === 0 || delta[i] === 0 || sign(delta[i - 1]) !== sign(delta[i])) {
                    derivatives[i] = 0;
                } else {
                    var w1 = 2 * h[i] + h[i - 1];
                    var w2 = h[i] + 2 * h[i - 1];
                    derivatives[i] = (w1 + w2) / (w1 / delta[i - 1] + w2 / delta[i]);
                }
            }
        }

        var count = Math.max(sampleCount || 400, clean.length);
        var curve = [];
        var segment = 0;
        var xMin = x[0];
        var xMax = x[x.length - 1];

        for (i = 0; i < count; i++) {
            var sampleX = xMin + (xMax - xMin) * i / (count - 1);
            while (segment < x.length - 2 && sampleX > x[segment + 1]) {
                segment++;
            }
            var segmentH = h[segment];
            var t = (sampleX - x[segment]) / segmentH;
            var t2 = t * t;
            var t3 = t2 * t;
            var sampleY = (2 * t3 - 3 * t2 + 1) * y[segment] +
                (t3 - 2 * t2 + t) * segmentH * derivatives[segment] +
                (-2 * t3 + 3 * t2) * y[segment + 1] +
                (t3 - t2) * segmentH * derivatives[segment + 1];
            curve.push({x: sampleX, y: sampleY});
        }

        return curve;
    }

    function formatNumber(value) {
        if (value === 0) {
            return '0';
        }
        if (Math.abs(value) >= 1e4 || Math.abs(value) < 1e-2) {
            return value.toExponential(3);
        }
        return value.toFixed(3);
    }

    function niceTicks(min, max, target) {
        if (min === max) {
            return [min];
        }
        var raw = (max - min) / (target || 7);
        var power = Math.pow(10, Math.floor(Math.log(raw) / Math.LN10));
        var scaled = raw / power;
        var multiplier = scaled <= 1 ? 1 : scaled <= 2 ? 2 : scaled <= 2.5 ? 2.5 : scaled <= 5 ? 5 : 10;
        var step = multiplier * power;
        var ticks = [];
        for (var value = Math.ceil(min / step) * step; value <= max + step * 1e-9; value += step) {
            ticks.push(Number(value.toPrecision(12)));
        }
        return ticks;
    }

    function render(holder, data) {
        holder.innerHTML = '';
        var points = (data.points || []).map(function(point) {
            return {x: Number(point.x), y: Number(point.y)};
        }).filter(function(point) {
            return isFinite(point.x) && isFinite(point.y);
        }).sort(function(a, b) { return a.x - b.x; });
        if (points.length < 2) {
            holder.textContent = 'Not enough plottable data.';
            return;
        }

        var curve = pchipCurve(points, 400);
        var curveLabel = data.curve_label || 'PCHIP interpolation';
        var xMin = points[0].x;
        var xMax = points[points.length - 1].x;
        var allY = points.concat(curve).map(function(point) { return point.y; });
        var rawYMin = Math.min.apply(null, allY);
        var rawYMax = Math.max.apply(null, allY);
        var ySpan = rawYMax - rawYMin;
        var yPadding = ySpan ? ySpan * 0.08 : Math.max(Math.abs(rawYMax) * 0.08, 1);
        var yMin = Math.min(0, rawYMin - yPadding);
        var yMax = rawYMax + yPadding;
        var plotWidth = WIDTH - MARGIN.left - MARGIN.right;
        var plotHeight = HEIGHT - MARGIN.top - MARGIN.bottom;
        var sx = function(value) {
            return MARGIN.left + (value - xMin) / (xMax - xMin) * plotWidth;
        };
        var sy = function(value) {
            return MARGIN.top + plotHeight - (value - yMin) / (yMax - yMin) * plotHeight;
        };

        var card = document.createElement('div');
        card.className = 'MoldChartCard';
        var title = document.createElement('h3');
        title.className = 'MoldChartTitle';
        title.textContent = data.title || '';
        card.appendChild(title);
        var wrap = document.createElement('div');
        wrap.className = 'MoldChartWrap';
        card.appendChild(wrap);
        var svg = svgElement('svg', {
            viewBox: '0 0 ' + WIDTH + ' ' + HEIGHT,
            role: 'img',
            'aria-label': data.title || 'Cross section chart'
        }, wrap);
        var tooltip = document.createElement('div');
        tooltip.className = 'MoldChartTooltip';
        wrap.appendChild(tooltip);
        holder.appendChild(card);

        niceTicks(xMin, xMax, 7).forEach(function(value) {
            var xPosition = sx(value);
            svgElement('line', {x1: xPosition, y1: MARGIN.top, x2: xPosition, y2: MARGIN.top + plotHeight, 'class': 'MoldChartGrid'}, svg);
            textElement(svg, xPosition, MARGIN.top + plotHeight + 24, value.toFixed(0), {'text-anchor': 'middle', 'class': 'MoldChartTick'});
        });
        for (var tick = 0; tick <= 6; tick++) {
            var yValue = yMin + (yMax - yMin) * tick / 6;
            var yPosition = sy(yValue);
            svgElement('line', {x1: MARGIN.left, y1: yPosition, x2: MARGIN.left + plotWidth, y2: yPosition, 'class': 'MoldChartGrid'}, svg);
            textElement(svg, MARGIN.left - 10, yPosition + 4, yValue.toExponential(1), {'text-anchor': 'end', 'class': 'MoldChartTick'});
        }

        var path = curve.map(function(point, index) {
            return (index ? 'L' : 'M') + sx(point.x).toFixed(2) + ',' + sy(point.y).toFixed(2);
        }).join(' ');
        svgElement('path', {d: path, fill: 'none', stroke: '#7c3aed', 'stroke-width': '2.4', 'class': 'MoldChartCurve'}, svg);
        svgElement('line', {x1: MARGIN.left, y1: MARGIN.top + plotHeight, x2: MARGIN.left + plotWidth, y2: MARGIN.top + plotHeight, 'class': 'MoldChartAxis'}, svg);
        svgElement('line', {x1: MARGIN.left, y1: MARGIN.top, x2: MARGIN.left, y2: MARGIN.top + plotHeight, 'class': 'MoldChartAxis'}, svg);
        textElement(svg, MARGIN.left + plotWidth / 2, HEIGHT - 18, data.x_label + ' [' + data.x_unit + ']', {'text-anchor': 'middle', 'font-size': '14', fill: '#344054'});
        var yLabel = textElement(svg, 24, MARGIN.top + plotHeight / 2, data.y_label + ' [' + data.y_unit + ']', {'text-anchor': 'middle', 'font-size': '14', fill: '#344054'});
        yLabel.setAttribute('transform', 'rotate(-90 24 ' + (MARGIN.top + plotHeight / 2) + ')');

        var legend = svgElement('g', {transform: 'translate(' + MARGIN.left + ',8)'}, svg);
        svgElement('rect', {x: 0, y: 0, width: 390, height: 34, rx: 6, fill: '#fff', stroke: '#d0d5dd'}, legend);
        svgElement('line', {x1: 12, y1: 17, x2: 37, y2: 17, stroke: '#7c3aed', 'stroke-width': 2.4}, legend);
        textElement(legend, 45, 21, curveLabel, {'class': 'MoldChartLegend'});
        svgElement('circle', {cx: 237, cy: 17, r: 3.5, fill: '#64748b', 'fill-opacity': 0.45}, legend);
        textElement(legend, 250, 21, data.point_label || 'Values from DB', {'class': 'MoldChartLegend'});

        var crosshair = svgElement('line', {x1: 0, y1: MARGIN.top, x2: 0, y2: MARGIN.top + plotHeight, 'class': 'MoldChartCrosshair'}, svg);
        var hit = svgElement('rect', {x: MARGIN.left, y: MARGIN.top, width: plotWidth, height: plotHeight, 'class': 'MoldChartHit'}, svg);

        function positionTooltip(event) {
            var box = wrap.getBoundingClientRect();
            var left = event.clientX - box.left + 14;
            var top = event.clientY - box.top - 18;
            if (left + 225 > box.width) {
                left -= 240;
            }
            tooltip.style.left = left + 'px';
            tooltip.style.top = Math.max(4, top) + 'px';
        }

        function hideTooltip() {
            tooltip.style.display = 'none';
            crosshair.style.opacity = 0;
        }

        function nearestCurve(value) {
            var index = Math.round((value - xMin) / (xMax - xMin) * (curve.length - 1));
            return curve[Math.max(0, Math.min(curve.length - 1, index))];
        }

        function nearestDb(value) {
            return points.reduce(function(nearest, point) {
                return Math.abs(point.x - value) < Math.abs(nearest.x - value) ? point : nearest;
            });
        }

        hit.addEventListener('pointermove', function(event) {
            var box = svg.getBoundingClientRect();
            var pixelX = (event.clientX - box.left) * WIDTH / box.width;
            var value = xMin + (pixelX - MARGIN.left) / plotWidth * (xMax - xMin);
            var predicted = nearestCurve(Math.max(xMin, Math.min(xMax, value)));
            var dbPoint = nearestDb(predicted.x);
            crosshair.setAttribute('x1', sx(predicted.x));
            crosshair.setAttribute('x2', sx(predicted.x));
            crosshair.style.opacity = 0.65;
            tooltip.innerHTML = '<b>' + curveLabel + '</b><br>' +
                data.x_label + ' = ' + formatNumber(predicted.x) + ' ' + data.x_unit + '<br>' +
                data.y_label + ' = ' + formatNumber(predicted.y) + ' ' + data.y_unit + '<br>' +
                '<span>Nearest DB value: ' + formatNumber(dbPoint.x) + ' ' + data.x_unit +
                ', ' + formatNumber(dbPoint.y) + ' ' + data.y_unit + '</span>';
            tooltip.style.display = 'block';
            positionTooltip(event);
        });
        hit.addEventListener('pointerleave', hideTooltip);

        var pointRadius = points.length > 100 ? 2.2 : 4;
        points.forEach(function(point, index) {
            var circle = svgElement('circle', {cx: sx(point.x), cy: sy(point.y), r: pointRadius, 'class': 'MoldChartDbPoint'}, svg);
            circle.addEventListener('pointerenter', function(event) {
                tooltip.innerHTML = '<b>DB value #' + (index + 1) + '</b><br>' +
                    data.x_label + ' = ' + formatNumber(point.x) + ' ' + data.x_unit + '<br>' +
                    data.y_label + ' = ' + formatNumber(point.y) + ' ' + data.y_unit;
                tooltip.style.display = 'block';
                positionTooltip(event);
            });
            circle.addEventListener('pointermove', positionTooltip);
            circle.addEventListener('pointerleave', hideTooltip);
        });
    }

    function formatPredictionNumber(value) {
        var number = Number(value);
        return isFinite(number) ? number.toExponential(6) : '';
    }

    function renderPrediction(holder, data) {
        holder.innerHTML = '';
        var points = (data.points || []).map(function(point) {
            return {x: Number(point.x), y: Number(point.y)};
        }).filter(function(point) {
            return isFinite(point.x) && isFinite(point.y);
        }).sort(function(a, b) {
            return a.x - b.x;
        });
        if (points.length < 2) {
            holder.textContent = 'Not enough plottable data.';
            return;
        }

        var selectedX = Number(data.selected_wavelength);
        var selectedY = Number(data.predicted_y);
        var curve = pchipCurve(points, 400);
        var allValues = curve.concat(points, [{x: selectedX, y: selectedY}]).map(function(point) {
            return point.y;
        }).filter(function(value) {
            return isFinite(value);
        });
        if (!allValues.length || !isFinite(selectedY)) {
            holder.textContent = 'The selected result cannot be displayed.';
            return;
        }

        var width = 860;
        var height = 470;
        var left = 105;
        var right = 28;
        var top = 68;
        var bottom = 72;
        var plotWidth = width - left - right;
        var plotHeight = height - top - bottom;
        var xMin = points[0].x;
        var xMax = points[points.length - 1].x;
        var rawYMin = Math.min.apply(null, allValues);
        var rawYMax = Math.max.apply(null, allValues);
        var ySpan = rawYMax - rawYMin;
        var yPadding = ySpan ? ySpan * 0.08 : Math.max(Math.abs(rawYMax) * 0.08, 1e-30);
        var yMin = Math.min(0, rawYMin - yPadding);
        var yMax = rawYMax + yPadding;
        if (yMin === yMax) {
            yMax = yMin + 1e-30;
        }

        function sx(value) {
            return left + (Number(value) - xMin) / (xMax - xMin) * plotWidth;
        }

        function sy(value) {
            return top + plotHeight - (Number(value) - yMin) / (yMax - yMin) * plotHeight;
        }

        var plot = document.createElement('div');
        plot.className = 'GprPlot';
        var svg = svgElement('svg', {
            viewBox: '0 0 ' + width + ' ' + height,
            role: 'img',
            'aria-label': 'Interpolated thermal cross section curve'
        }, plot);
        holder.appendChild(plot);

        textElement(svg, width / 2, 22, data.title || '', {
            'text-anchor': 'middle',
            'class': 'GprPlotTitle'
        });

        for (var tick = 0; tick <= 4; tick++) {
            var xTickValue = xMin + (xMax - xMin) * tick / 4;
            var xTick = sx(xTickValue);
            var yTickValue = yMin + (yMax - yMin) * tick / 4;
            var yTick = sy(yTickValue);
            svgElement('line', {x1: xTick, y1: top, x2: xTick, y2: top + plotHeight, 'class': 'GprGrid'}, svg);
            svgElement('line', {x1: left, y1: yTick, x2: left + plotWidth, y2: yTick, 'class': 'GprGrid'}, svg);
            textElement(svg, xTick, top + plotHeight + 22, xTickValue.toFixed(0), {'text-anchor': 'middle', 'class': 'GprTick'});
            textElement(svg, left - 10, yTick + 4, formatPredictionNumber(yTickValue), {'text-anchor': 'end', 'class': 'GprTick'});
        }

        var curvePath = curve.map(function(point) {
            return (point === curve[0] ? 'M' : 'L') +
                sx(point.x).toFixed(2) + ',' + sy(point.y).toFixed(2);
        }).join(' ');
        svgElement('path', {d: curvePath, fill: 'none', 'class': 'GprCurve'}, svg);

        var pointRadius = points.length > 100 ? 2.0 : 3.2;
        points.forEach(function(point) {
            svgElement('circle', {
                cx: sx(point.x),
                cy: sy(point.y),
                r: pointRadius,
                'class': 'GprObservedPoint'
            }, svg);
        });

        var selectedPlotX = sx(selectedX);
        var selectedPlotY = sy(selectedY);
        svgElement('line', {x1: selectedPlotX, y1: top, x2: selectedPlotX, y2: top + plotHeight, 'class': 'GprSelectedGuide'}, svg);
        svgElement('line', {x1: left, y1: selectedPlotY, x2: selectedPlotX, y2: selectedPlotY, 'class': 'GprSelectedGuide'}, svg);
        svgElement('circle', {cx: selectedPlotX, cy: selectedPlotY, r: 6, 'class': 'GprSelectedPoint'}, svg);
        textElement(svg, selectedPlotX, top + plotHeight + 42, selectedX + ' ' + data.x_unit, {'text-anchor': 'middle', 'class': 'GprSelectedTick'});
        textElement(svg, left - 10, selectedPlotY + 4, formatPredictionNumber(selectedY), {'text-anchor': 'end', 'class': 'GprSelectedTick'});
        svgElement('line', {x1: left, y1: top + plotHeight, x2: left + plotWidth, y2: top + plotHeight, 'class': 'GprAxis'}, svg);
        svgElement('line', {x1: left, y1: top, x2: left, y2: top + plotHeight, 'class': 'GprAxis'}, svg);
        textElement(svg, left + plotWidth / 2, height - 14, data.x_label + ' [' + data.x_unit + ']', {'text-anchor': 'middle', 'class': 'GprAxisLabel'});
        var axisLabel = svgElement('text', {
            transform: 'translate(20 ' + (top + plotHeight / 2) + ') rotate(-90)',
            'text-anchor': 'middle',
            'class': 'GprAxisLabel'
        }, svg);
        axisLabel.textContent = data.y_label + ' [' + data.y_unit + ']';

        var legend = svgElement('g', {'class': 'GprLegend'}, svg);
        svgElement('line', {x1: left + 10, y1: 45, x2: left + 38, y2: 45, 'class': 'GprCurve'}, legend);
        textElement(legend, left + 44, 49, data.prediction_curve_label || 'PCHIP interpolation');
        svgElement('circle', {cx: left + 190, cy: 45, r: 3.2, 'class': 'GprObservedPoint'}, legend);
        textElement(legend, left + 200, 49, 'Database data');
        svgElement('circle', {cx: left + 326, cy: 45, r: 5, 'class': 'GprSelectedPoint'}, legend);
        textElement(legend, left + 338, 49, 'Selected prediction');
    }

    window.MoldInteractiveChart = {
        render: render,
        renderPrediction: renderPrediction,
        pchipCurve: pchipCurve
    };
})(window, document);
