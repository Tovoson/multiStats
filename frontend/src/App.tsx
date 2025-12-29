function App() {
  const menu = [
    { name: "Home", link: "/" },
    { name: "About", link: "/about" },
    { name: "Contact", link: "/contact" },
  ];

  return (
    <div className="h-full w-full flex flex-col top-0" data-theme="light">
      <div className="flex justify-between py-5 px-30 border-b border-zinc-200">
        <div className="text-3xl font-bold">Logo</div>
        <div>
          {menu.map((item) => (
            <a
              key={item.name}
              href={item.link}
              className="mx-4 text-lg text-zinc-600 font-semibold hover:underline hover:text-primary transition-colors duration"
            >
              {item.name}
            </a>
          ))}
        </div>
      </div>
      <div className="bg-zinc-100 w-full h-screen rounded-lg flex items-center justify-center glass">
        <p className="text-primary/50">Hello react</p>
        <p>Lorem ipsum dolor sit amet consectetur adipisicing elit. Fugit neque qui voluptatem. Maxime distinctio ullam enim inventore quidem numquam modi accusamus rerum autem. Illum, maxime nam unde modi odit nulla.</p>
      </div>
      <div className="h-screen">
        <div>
          {/* Main content goes here */}
          <form action="">
            <input type="text" placeholder="Type here" className="input input-bordered w-full max-w-xs" />
          </form>
        </div>
      </div>
      <div className="">
        <footer className="footer footer-center p-4 bg-zinc-300 text-base-content rounded">
          <div>
            <p>Copyright © 2024 - All right reserved by Your Company</p>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default App;
