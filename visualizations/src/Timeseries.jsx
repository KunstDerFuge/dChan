import React from 'react'
import {scaleLinear} from 'd3-scale'
import {extent} from 'd3-array'
import {curveMonotoneX, line} from 'd3-shape'
import axios from 'axios'
import {scaleTime} from 'd3'
import * as d3 from 'd3'

const Timeseries = (props) => {
  const {
    width,
    height
  } = props

  const [data, setData] = React.useState([])
  const [agg, setAgg] = React.useState('week')
  const [perMille, setPerMille] = React.useState(true)
  const [keywords, setKeywords] = React.useState('LARP')

  const fetchData = () => {
    axios.get('http://localhost:8000/data', {params: {keywords: keywords, agg: agg}}).then((res) => {
      setData(res.data.data.posts_over_time.buckets)
      console.log(data)
    }).catch((e) => console.log(e))
  }

  React.useEffect(() => {
    fetchData()
  }, [agg, perMille])

  React.useEffect(() => {
    const xScale = scaleTime()
      .domain(extent(data, datum => new Date(datum.key)))
      .range([50, width])

    const yScale = scaleLinear()
      .domain(extent(data, datum => {
        if (datum.doc_count === 0) {
          return 0
        }
        else if (perMille) {
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
      .text(`Posts by ${agg} matching phrase "${keywords}" ${perMille ? 'per 1000 posts' : ''}`)

    // y axis label
    svg.select('.y-label')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0)
      .attr('x', 0 - (height / 2))
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .text('')

  }, [data])

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
        <label>Keywords:
          &nbsp;
          <input style={{fontSize: '1em'}} value={keywords} onChange={(event => {
            setKeywords(event.target.value)
          })}/>
        </label>
        &nbsp;
        <label>Aggregate Interval:
          &nbsp;
          <select name="interval" id="interval" value={agg} onChange={(event) => {
            setAgg(event.target.value)
          }}>
            <option value="day">Day</option>
            <option value="week">Week</option>
            <option value="month">Month</option>
          </select>
          <select name="interval" id="interval" value={perMille ? 'perMille' : 'total'} onChange={(event) => {
            console.log(event.target.value)
            setPerMille(event.target.value === 'perMille')
          }}>
            <option value="perMille">Per 1000 posts</option>
            <option value="total">Total volume</option>
          </select>
        </label>
      </form>
    </>
  )
}

export default Timeseries