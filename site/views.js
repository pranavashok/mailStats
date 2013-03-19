/**
 * Data object for email data pulled by the python script
 * Triggers updates to the graph views when data changes are made
 */
var emailData = (function(emailsbydate, threadLinks, authors) {
    var obj = {byDate:emailsbydate, threadLinks: threadLinks, authors: authors, deSelectedAuthors: []};
    obj.getByDate = function() {
        return this.byDate;
    };
    obj.getThreadLinks = function() {
        return this.threadLinks;
    };
    obj.getAuthors = function() {
        return this.authors;
    };
    obj.removeAuthor = function(author) {
        this.deSelectedAuthors.push(author);
        $(this).trigger("authorUpdate");
    };
    obj.addAuthor = function(author) {
        var idx = this.deSelectedAuthors.indexOf(author);
        this.deSelectedAuthors.splice(idx,1);
        $(this).trigger("authorUpdate");
    };
    obj.getDeSelectedAuthors = function() {
        return this.deSelectedAuthors;
    };
    obj.changeAll = function(selectAll) {
        if(selectAll) {
            this.deSelectedAuthors = [];
        } else {
            //copy authors array
            this.deSelectedAuthors = this.authors.slice();
        }
        $(this).trigger("authorUpdate");
    };
    return obj;
}(emailsbydate, threadlinks, authors));


var graphView = (function(data, el) {
    var obj = {data:data, el:el};
    $(obj.data).on("authorUpdate", function(evt, filter) {
        obj.updateData(250,filter);
    });
    obj.updateData = function(duration, filter) {
        if(filter !== undefined) this.filter = filter;
        this.svg.select("path.line")
            .datum(_.pairs(this.data.getByDate()).sort())
            .transition(duration)
            .attr("d", this.line);

        var circle = this.svg.selectAll("circle")
            .data(_.pairs(this.data.getByDate()).sort());

        circle.enter().append("circle");
        circle.transition().duration(duration)
            .attr("r","3")
            .attr("cx",function(d) { return obj.x(new Date(parseInt(d[0])));})
            .attr("cy",function(d) { return obj.yFunc(d) });

        circle.exit().remove();

    };
    obj.yFunc = function(d) {
        var count = 0;
        for(var em in d[1]) {
            if((this.filter != undefined && this.filter != "" && d[1][em]["from"].toLowerCase().indexOf(this.filter) == -1) ||
                this.data.getDeSelectedAuthors().indexOf(d[1][em]["from"]) != -1) continue;
            count++;
        }
        return this.y(count)-5;
    };
    obj.render = function() {
        var margin = {top: 20, right: 20, bottom: 30, left: 50},
            width = 460 - margin.left - margin.right,
            height = 250 - margin.top - margin.bottom;

        this.x = d3.time.scale()
            .range([0,width])
            .domain(d3.extent(_.map(_.keys(obj.data.getByDate()), function(d) { return new Date(parseInt(d))})));
        this.y = d3.scale.linear()
            .range([height,0])
            .domain(d3.extent(_.map(obj.data.getByDate(),function(val,idx) { return val.length })));

        var xAxis = d3.svg.axis()
            .scale(this.x)
            .orient("bottom");

        var yAxis = d3.svg.axis()
            .scale(this.y)
            .orient("left");

        this.line = d3.svg.line()
            .x(function(d) { return obj.x(new Date(parseInt(d[0]))); })
            .y(function(d) { return obj.yFunc(d) });

        this.svg = d3.select(obj.el).append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        this.svg.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + height + ")")
            .call(xAxis);

        this.svg.append("g")
            .attr("class", "y axis")
            .call(yAxis)
            .append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", 6)
            .attr("dy", ".71em")
            .style("text-anchor", "end")
            .text("# of Emails");

        this.svg.append("path")
            .attr("class", "line")
            .datum(_.pairs(this.data.getByDate()).sort())
            .attr("d", this.line);

        this.updateData(0);

    };
    return obj;
}(emailData,"#emailtotals"));

var threadView = (function(emailData, el) {
    var obj = {data:emailData, el:el};
    obj.update = function(filter) {
        var newLinks = [];
        this.data.getThreadLinks().forEach(function(link) {
            if(obj.data.getDeSelectedAuthors().indexOf(link.target.email) == -1 &&
                 (filter == "" || filter == undefined || (filter != undefined && filter != "" && link.target.email.indexOf(filter) != -1))) {
                newLinks.push(link);
            }
        });
        this.links = newLinks;
        this.force.links(this.links)

        var path = this.svg.selectAll("path")
            .data(obj.force.links());

        path.enter().append("svg:path")
            .attr("marker-end","url(#response)");
        path.exit().remove();

        this.force.start()
    };
    $(obj.data).on("authorUpdate", function(evt, filter) {
        if(filter != undefined) obj.filter = filter;
        obj.update(obj.filter);
    });
    obj.render = function() {
        //adapted from http://bl.ocks.org/mbostock/1153292
        var w = 960,
            h = 500;

        this.nodes = {};
        this.links = obj.data.getThreadLinks().slice();
        this.links.forEach(function(link) {
            link.source = obj.nodes[link.source] || (obj.nodes[link.source] = {email: link.source});
            link.target = obj.nodes[link.target] || (obj.nodes[link.target] = {email: link.target});
        });
        this.force = d3.layout.force()
            .nodes(d3.values(obj.nodes))
            .links(obj.links)
            .size([w, h])
            .linkDistance(180)
            .charge(-200)
            .on("tick", tick);

        this.svg = d3.select(el).append("svg:svg")
            .attr("width",w)
            .attr("height",h);

        this.svg.append("svg:defs")
            .append("svg:marker")
            .attr("id", "response")
            .attr("viewBox", "0 0 20 20")
            .attr("refX", 0)
            .attr("refY", 10)
            .attr("markerWidth", 8)
            .attr("markerHeight", 6)
            .attr("markerUnits","strokeWidth")
            .attr("orient", "auto")
            .append("svg:path")
            .attr("d", "M 0 0 L 20 10 L 0 20 z");

        var path = this.svg.append("svg:g").selectAll("path")
            .data(obj.force.links())
            .enter().append("svg:path")
            .attr("marker-end","url(#response)");

        var circle = this.svg.append("svg:g").selectAll("circle")
            .data(obj.force.nodes())
            .enter().append("svg:circle")
            .attr("r",6)
            .call(obj.force.drag);

        var text = this.svg.append("svg:g").selectAll("g")
            .data(obj.force.nodes())
            .enter().append("svg:g");

        text.append("svg:text")
            .attr("x", 20)
            .attr("y", ".31em")
            .text(function(d) { return d.email; });

        function tick() {
            path.attr("d", function(d) {
                var dx = d.target.x - d.source.x,
                    dy = d.target.y - d.source.y,
                    dr = 0
                return "M" + d.source.x + "," + d.source.y + "," + d.target.x + "," + d.target.y;
            });

            circle.attr("transform", function(d) {
                return "translate(" + d.x + "," + d.y + ")";
            });

            text.attr("transform", function(d) {
                return "translate(" + d.x + "," + d.y + ")";
            });
        }
        this.force.start();
    };
    return obj;
}(emailData, "#threadGraph"));

var authorView = (function(emailData, el) {
    var obj = {data: emailData, el: el};
    obj.render = function() {
        $(obj.el).html("<input id='dataListFilter' type='text' />" +
            "<span class='selectall'>Select All</span><span class='deselectall'>Deselect All</span><ul></ul>");
        $(obj.el).click(function(evt) {
            var target = $(evt.target);
            console.log(evt);
            if(evt.target.tagName == "LI") {

                if(target.hasClass("selected")) {
                    obj.data.removeAuthor(target.text());
                    target.removeClass("selected");
                } else {
                    obj.data.addAuthor(target.text());
                    target.addClass("selected");
                }
            } else if(evt.target.tagName == "SPAN") {
                obj.data.changeAll(target.hasClass("selectall"));
                obj.filter($(obj.el).find("input").val());
            }
        });
        $(obj.el).keyup(function(evt) {
            if(evt.target.tagName == "INPUT") {
                obj.filter(evt.target.value.toLowerCase());
                $(obj.data).trigger("authorUpdate",evt.target.value.toLowerCase());
            }
        });
        this.filter("");
    };
    obj.filter = function(filter) {
        var list = "";
        for(var author in this.data.getAuthors()) {
            if(filter != "" && this.data.getAuthors()[author].toLowerCase().indexOf(filter) == -1) continue;
            list += "<li ";
            list += this.data.getDeSelectedAuthors().indexOf(this.data.getAuthors()[author]) == -1 ? "class='selected'" : "";
            list += ">"+this.data.getAuthors()[author].replace("<","&lt;").replace(">","&gt;")+"</li>";
        }
        $(obj.el).find("ul").html(list);
    };
    return obj;
}(emailData,"#datalist"));

$(document).ready(function() {
    graphView.render();
    authorView.render();
    threadView.render();
});