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
  const [startDate, setStartDate] = React.useState('')
  const [endDate, setEndDate] = React.useState('')
  const [timezone, setTimezone] = React.useState('America/Los_Angeles')
  const [width, setWidth] = React.useState(600)
  const [height, setHeight] = React.useState(600)

  const matches = data.length > 0 ? data.reduce((previousValue, curr) => previousValue + curr.keywords_filter.doc_count, 0) : 0
  const total = data.length > 0 ? data.reduce((previousValue, curr) => previousValue + curr.total.value, 0) : 0
  const percent = matches / total * 100

  const hour_enabled = startDate !== '' && endDate !== '' &&
    (new Date(endDate).getTime() - new Date(startDate).getTime()) / (1000 * 3600 * 24) <= 120 // Only enable if range <= 120 days

  const usefulDates = [
    {date: '2017-10-28', description: <>First Q drop</>},
    {date: '2017-11-09', description: <>Q uses tripcode for the first time; <code>!ITPb.qbhqo</code> (Matlock)</>},
    {
      date: '2018-01-03',
      description: <>Dispute over the veracity of the Q poster; Ron verifies Q without a tripcode</>
    },
    {date: '2020-12-08', description: <>Final Q drop</>}
  ]

  const simple_operators = [
    {operator: <><code>+</code></>, description: <>signifies AND operation</>},
    {operator: <><code>|</code></>, description: <>signifies OR operation</>},
    {operator: <><code>-</code></>, description: <>negates a single token</>},
    {operator: <><code>"</code></>, description: <>wraps a number of tokens to signify a phrase for searching</>},
    {operator: <><code>*</code></>, description: <>at the end of a term signifies a prefix query</>},
    {operator: <><code>(</code> and <code>)</code></>, description: <>signify precedence</>},
    {operator: <><code>~N</code></>, description: <>after a word signifies edit distance (fuzziness)</>},
    {operator: <><code>~N</code></>, description: <>after a phrase signifies slop amount</>}
  ]

  const advanced_operators = [
    {
      operator: <><code>field_name: query</code></>,
      description: <>Query a specific field; see below for available fields</>
    },
    {
      operator: <><code>/regex/</code></>,
      description: <>Attempt to search via regular expressions; see limitations <a
        href="https://www.elastic.co/guide/en/elasticsearch/reference/current/regexp-syntax.html"
        target="_blank">here</a></>
    },
    {operator: <><code>AND</code></>, description: <>signifies AND operation</>},
    {operator: <><code>OR</code></>, description: <>signifies OR operation</>},
    {operator: <><code>"</code></>, description: <>wraps a number of tokens to signify a phrase for searching</>},
    {operator: <><code>(</code> and <code>)</code></>, description: <>signify precedence</>}
  ]

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
    axios.get('https://dchan.qorigins.org/data/', {
      params: {
        keywords: keywords,
        agg: !hour_enabled && agg === 'hour' ? 'day' : agg,
        syntax: syntax,
        start_date: startDate,
        end_date: endDate,
        timezone: timezone
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
      .domain(extent(data, datum => new Date(datum.key_as_string)))
      .range([60, width])

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
      .attr('transform', `translate(55, 0)`)
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

    // Chart subtitle
    svg.select('.subtitle')
      .attr('x', width / 2)
      .attr('y', 35)
      .style('text-anchor', 'middle')
      .text(`${startDate && 'from ' + startDate} ${endDate && 'to ' + endDate}`)


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
        <text className="subtitle"/>
        <text className="y-label"/>
      </svg>
      {
        data.length > 0 &&
        <>
          <p style={{paddingTop: '6px'}}>Matched {matches.toLocaleString()} of {total.toLocaleString()} —&nbsp;
            {
              percent > 25 ? percent.toFixed(0)
                : percent > 1 ? percent.toFixed(1)
                  : percent > 0.01 ? percent.toFixed(2)
                    : percent.toFixed(3)
            }% of total
          </p>
        </>
      }
      <form onSubmit={(event => {
        event.preventDefault()
        fetchData()
      })}>
        <div className="row g-2">
          <div className="col-md-6">
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
              {hour_enabled && <option value="hour">Hour</option>}
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
          <div className="row g-2">
            <div className="col-md-auto">
              <label htmlFor="date-start" className="form-label">Start Date</label>
              <input id="date-start" type="date" className="form-control" aria-label="Start Date"
                     aria-describedby="date-start" placeholder="YYYY-MM-DD" value={startDate}
                     onChange={(e) => setStartDate(e.target.value)}/>
            </div>
            <div className="col-md-auto">
              <label htmlFor="date-end" className="form-label">End Date</label>
              <input id="date-end" type="date" className="form-control" aria-label="End Date"
                     aria-describedby="date-end" placeholder="YYYY-MM-DD" value={endDate}
                     onChange={(e) => setEndDate(e.target.value)}/>
            </div>
            <div className="col-md-auto">
              <label htmlFor="timezone" className="form-label">Time Zone</label>
              <select className="form-select" name="timezone" id="timezone" value={timezone} onChange={(event) => {
                setTimezone(event.target.value)
              }}>
                <option value="America/Los_Angeles">America/Los_Angeles</option>
                <option value="US/Central">US/Central</option>
                <option value="US/Eastern">US/Eastern</option>
                <option value="UTC">UTC</option>
                <option value="Etc/GMT+8">Etc/GMT+8</option>
              </select>
            </div>
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
          <p>See hints and allowed operators for&nbsp;
            <code>query_string</code> <a target="_blank"
                                         href="https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-query-string-query.html#query-string-syntax">here</a>.
          </p>
      }
      <div className="accordion" id="hints-accordion">
        <div className="accordion-item">
          <h2 className="accordion-header" id="syntax-tips-label">
            <button className="accordion-button collapsed" type="button" data-bs-toggle="collapse"
                    data-bs-target="#syntax-tips" aria-expanded="false" aria-controls="syntax-tips">
              Syntax Tips
            </button>
          </h2>
          <div id="syntax-tips" className="accordion-collapse collapse" aria-labelledby="syntax-tips-label"
               data-bs-parent="#hints-accordion">
            <div className="accordion-body">
              <table className="table">
                <thead>
                <tr>
                  <th scope="col">Operator</th>
                  <th scope="col">Description</th>
                </tr>
                </thead>
                <tbody>
                {
                  syntax === 'simple' ?
                    simple_operators.map((tip) => {
                      return (
                        <tr>
                          <td>{tip.operator}</td>
                          <td>{tip.description}</td>
                        </tr>
                      )
                    })
                    :
                    advanced_operators.map((tip) => {
                      return (
                        <tr>
                          <td>{tip.operator}</td>
                          <td>{tip.description}</td>
                        </tr>
                      )
                    })
                }
                </tbody>
              </table>
            </div>
          </div>
        </div>
        <div className="accordion-item">
          <h2 className="accordion-header" id="useful-dates-label">
            <button className="accordion-button collapsed" type="button" data-bs-toggle="collapse"
                    data-bs-target="#useful-dates" aria-expanded="false" aria-controls="useful-dates">
              Useful Dates
            </button>
          </h2>
          <div id="useful-dates" className="accordion-collapse collapse" aria-labelledby="useful-dates-label"
               data-bs-parent="#hints-accordion">
            <div className="accordion-body">
              <table className="table">
                <thead>
                <tr>
                  <th scope="col">Date</th>
                  <th scope="col">Description</th>
                </tr>
                </thead>
                <tbody>
                {
                  usefulDates.map((date) => {
                    return (
                      <tr>
                        <td>{date.date}</td>
                        <td>{date.description}</td>
                      </tr>
                    )
                  })
                }
                </tbody>
              </table>
            </div>
          </div>
        </div>
        {
          syntax === 'advanced' &&
          <div className="accordion-item">
            <h2 className="accordion-header" id="fields-available-label">
              <button className="accordion-button collapsed" type="button" data-bs-toggle="collapse"
                      data-bs-target="#fields-available" aria-expanded="false" aria-controls="fields-available">
                Fields Available
              </button>
            </h2>
            <div id="fields-available" className="accordion-collapse collapse" aria-labelledby="fields-available-label"
                 data-bs-parent="#hints-accordion">
              <div className="accordion-body">
                <table className="table">
                  <thead>
                  <tr>
                    <th scope="col">Field</th>
                    <th scope="col">Description</th>
                  </tr>
                  </thead>
                  <tbody>
                  <tr>
                    <td>platform.name</td>
                    <td><code>4chan</code> or <code>8kun</code>. Note: posts sourced from 8chan are encoded as 8kun.
                    </td>
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
                    <td>The hash after "ID:" identifying a poster within a thread. Note: some boards have disabled
                      poster
                      IDs.
                    </td>
                  </tr>
                  <tr>
                    <td>subject</td>
                    <td>The subject line of a post.</td>
                  </tr>
                  <tr>
                    <td>body</td>
                    <td>The actual comment in a post as a user would have typed it, including formatting syntax.
                    </td>
                  </tr>
                  <tr>
                    <td>is_op</td>
                    <td>One of <code>true</code> or <code>false</code>; whether a post is an OP.</td>
                  </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        }
      </div>
      <br/>
      <p>See notes on how we collected this data as well as some caveats and tips for its use <a
        href="/about/#timeseries" target="_blank">here</a>.</p>
      <br/>
    </>
  )
}

export default Timeseries