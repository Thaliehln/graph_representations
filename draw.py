        '''
        g = create_graph(test)
        nx.draw(g)
        plt.savefig(r'C:\Users\langhe\switchdrive\Private\Unisanté\epoct_variables\graph_{}.png'.format(fd.getID())) # save as png
        paragraph = doc.add_paragraph()
        run2 = paragraph.add_run()
        inline_shape = run2.add_inline_picture(r'C:\Users\langhe\switchdrive\Private\Unisanté\epoct_variables\graph.png')
        inline_shape.width = 400
        inline_shape.height = 300
        '''