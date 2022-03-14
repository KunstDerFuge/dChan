function replaceChanLinks() {
  let regex = /(https:\/\/8(ch|kun)\.[a-zA-Z]{2,3})/i

  for (let i = 0; i < document.links.length; i++) {
    let link = document.links[i]
    if (link.href !== undefined) {
      link.setAttribute('href', link.href.replace(regex, ''))
    }
  }
}

replaceChanLinks()
document.addEventListener("DOMContentLoaded", replaceChanLinks)
