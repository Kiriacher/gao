const sliderMain = new Swiper('.slider_main',{
    freeMode: true,
    centeredSlides: true,
    mousewheel: true,
    parallax: true,
    breakpoints: {
        680: {
            slidesPerViev: 3.5,
            spaceBetween: 50
        }
    }
})

const sliderMain1 = new Swiper('.slider_main1',{
    freeMode: true,
    centeredSlides: true,
    mousewheel: true,
    parallax: true,
    breakpoints: {
        680: {
            slidesPerViev: 3.5,
            spaceBetween: 50
        }
    }
})

sliderMain.controller.control = sliderMain1
sliderMain1.controller.control = sliderMain

