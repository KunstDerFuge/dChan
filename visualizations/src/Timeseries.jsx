import React from 'react'
import {scaleLinear} from 'd3-scale'
import {extent} from 'd3-array'
import {curveMonotoneX, line} from 'd3-shape'
import axios from 'axios'
import {scaleTime} from 'd3'
import * as d3 from 'd3'

const Timeseries = (props) => {
  const [data, setData] = React.useState([])
  const [agg, setAgg] = React.useState('week')
  const [perMille, setPerMille] = React.useState(true)
  const [keywords, setKeywords] = React.useState('LARP')
  const [syntax, setSyntax] = React.useState('simple')
  const [width, setWidth] = React.useState(600)
  const [height, setHeight] = React.useState(600)

  React.useEffect(() => {
    const resizeListener = () => {
      console.log('Updating size...')
      setWidth(props.parent.current.offsetWidth - 30)
      setHeight(width * 0.6)
      console.log(width, height)
    }
    window.addEventListener('resize', resizeListener)
    return () => {
      window.removeEventListener('resize', resizeListener)
    }
  }, [])

  const fetchData = () => {
    axios.get('https://dchan.qorigins.org/data', {
      params: {
        keywords: keywords,
        agg: agg,
        syntax: syntax
      }
    }).then((res) => {
      setData(res.data.data.posts_over_time.buckets)
      console.log(data)
    }).catch((e) => console.log(e))
  }

  React.useEffect(() => {
    setWidth(props.parent.current.offsetWidth)
    setHeight(width * 0.6)
    console.log(width, height)
  }, [props.parent])

  React.useEffect(() => {
    fetchData()
  }, [agg])

  React.useEffect(() => {
    const xScale = scaleTime()
      .domain(extent(data, datum => new Date(datum.key)))
      .range([50, width])

    const yScale = scaleLinear()
      .domain(extent(data, datum => {
        if (datum.doc_count === 0) {
          return 0
        } else if (perMille) {
          return datum.per_mille.value
        } else {
          return datum.keywords_filter.doc_count
        }
      }))
      .range([height, 40])

    const path = line()
      .x(datum => xScale(datum.key))
      .y(datum => yScale(datum.doc_count === 0 ? 0 : perMille ? datum.per_mille.value : datum.keywords_filter.doc_count))
      .curve(curveMonotoneX)

    var svg = d3.select('#chart')
    const xAxis = d3.axisBottom(xScale)
    const yAxis = d3.axisLeft(yScale)
    svg.select('.x-axis')
      .attr('transform', `translate(0, ${height + 5})`)
      .call(xAxis)

    svg.select('.y-axis')
      .attr('transform', `translate(45, 0)`)
      .call(yAxis)

    svg
      .selectAll('.line')
      .data([data])
      .join('path')
      .attr('class', 'line')
      .attr('d', path)
      .attr('fill', 'none')
      .attr('stroke', 'darkblue')
      .attr('stroke-width', '2')

    // Chart title
    svg.select('.title')
      .attr('x', width / 2)
      .attr('y', 20)
      .style('text-anchor', 'middle')
      .text(`Posts by ${agg} ${perMille ? 'per 1000 posts ' : ''} matching query: ${keywords}`)

    // y axis label
    svg.select('.y-label')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0)
      .attr('x', 0 - (height / 2))
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .text('')

  }, [data, perMille])

  return (
    <>
      <svg id="chart" width={width + 30} height={height + 30}>
        <g className="x-axis"/>
        <g className="y-axis"/>
        <text className="title"/>
        <text className="y-label"/>
      </svg>
      <form onSubmit={(event => {
        event.preventDefault()
        fetchData()
      })}>
        <div class="row g-2">
          <div class="col-md-6">
            <label htmlFor="query" className="form-label">Query</label>
            <input id="query" type="text" className="form-control" aria-label="Query"
                   aria-describedby="query" value={keywords} onChange={(e) => setKeywords(e.target.value)}/>
          </div>
          <div className="col-auto">
            <label htmlFor="agg" className="form-label">Syntax</label>
            <select className="form-select" name="syntax" id="syntax" value={syntax} onChange={(event) => {
              setSyntax(event.target.value)
            }}>
              <option value="simple">Simple</option>
              <option value="advanced">Advanced</option>
            </select>
          </div>
          <div className="col-md-2">
            <label htmlFor="agg" className="form-label">Aggregate Interval</label>
            <select className="form-select" name="agg" id="agg" value={agg} onChange={(event) => {
              setAgg(event.target.value)
            }}>
              <option value="day">Day</option>
              <option value="week">Week</option>
              <option value="month">Month</option>
            </select>
          </div>
          <div className="col-md-auto">
            <label htmlFor="interval" className="form-label">Mode</label>
            <select className="form-select" name="interval" id="interval" value={perMille ? 'perMille' : 'total'}
                    onChange={(event) => {
                      console.log(event.target.value)
                      setPerMille(event.target.value === 'perMille')
                    }}>
              <option value="perMille">Per 1000 posts</option>
              <option value="total">Total volume</option>
            </select>
          </div>
        </div>
      </form>
      <br/>
      {
        syntax === 'simple' ?
          <p>See hints and allowed operators for&nbsp;
            <code>simple_query_string</code> <a target="_blank"
                                                href="https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-simple-query-string-query.html#simple-query-string-syntax">here</a>.
          </p>
          :
          <>
            <p>See hints and allowed operators for&nbsp;
              <code>query_string</code> <a target="_blank"
                                           href="https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-query-string-query.html#query-string-syntax">here</a>.
            </p>
            <table class="table">
              <thead>
              <tr>
                <th scope="col">Field</th>
                <th scope="col">Description</th>
              </tr>
              </thead>
              <tbody>
              <tr>
                <td>platform.name</td>
                <td><code>4chan</code> or <code>8kun</code>. Note: posts sourced from 8chan are encoded as 8kun.</td>
              </tr>
              <tr>
                <td>board.name</td>
                <td>Name of the board a post belongs to.</td>
              </tr>
              <tr>
                <td>thread_id</td>
                <td>The unique number of the thread a post belongs to.</td>
              </tr>
              <tr>
                <td>post_id</td>
                <td>The unique number of a post.</td>
              </tr>
              <tr>
                <td>author</td>
                <td>The name of the poster, usually "Anonymous". Note: default names differ depending on board
                  settings.
                </td>
              </tr>
              <tr>
                <td>tripcode</td>
                <td>The tripcode on a post, if any.</td>
              </tr>
              <tr>
                <td>poster_hash</td>
                <td>The hash after "ID:" identifying a poster within a thread. Note: some boards have disabled poster
                  IDs.
                </td>
              </tr>
              <tr>
                <td>subject</td>
                <td>The subject line of a post.</td>
              </tr>
              <tr>
                <td>body</td>
                <td>The actual comment in a post as a user would have typed it, including formatting syntax.</td>
              </tr>
              <tr>
                <td>is_op</td>
                <td>One of <code>true</code> or <code>false</code>; whether a post is an OP.</td>
              </tr>
              </tbody>
            </table>
          </>
      }
      <br/>
    </>
  )
}

export default Timeseries