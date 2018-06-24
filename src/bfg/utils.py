import collections


def namedtuple_with_defaults(typename, field_names, default_values=()):
    T = collections.namedtuple(typename, field_names)
    T.__new__.__defaults__ = (None,) * len(T._fields)
    if isinstance(default_values, collections.Mapping):
        prototype = T(**default_values)
    else:
        prototype = T(*default_values)
    T.__new__.__defaults__ = tuple(prototype)
    return T


def mapper(namedtup, source):
    kwargs = {k: v for k, v in source.items() if k in namedtup._fields}
    return namedtup(**kwargs)


class Ladder:
    def __init__(self):
        self.ladder = self.get_ladder()
        self.index = range(len(self.ladder))
        self.ladder_dict = dict(zip(self.ladder, self.index))

    def __len__(self):
        return len(self.index)

    def __getitem__(self, item):
        '''
        Given a odds returns the ladder index where this item is
        '''
        return self.ladder_dict[item]

    def levels(self, start, levels=1, direction='back'):
        '''
        Return the odds from start to start+levels
        If direction is up returns
        '''
        # TODO not sure the direction is right for up and down?
        # TODO make sure we can go outsite range of list now i get an empty list if im outside bounds!
        assert direction in ('back', 'lay'), 'direction must be back or lay'
        if direction is 'back':
            return self.ladder[start:start + levels]
        elif direction is 'lay':
            return self.ladder[start - levels + 1:start + 1]

    @staticmethod
    def get_ladder():
        ladder = [1.01, 1.02, 1.03, 1.04, 1.05, 1.06, 1.07, 1.08, 1.09, 1.10, 1.11, 1.12, 1.13, 1.14, 1.15,
                  1.16, 1.17, 1.18, 1.19, 1.20, 1.21, 1.22, 1.23, 1.24, 1.25, 1.26, 1.27, 1.28, 1.29, 1.30,
                  1.31, 1.32, 1.33, 1.34, 1.35, 1.36, 1.37, 1.38, 1.39, 1.40, 1.41, 1.42, 1.43, 1.44, 1.45,
                  1.46, 1.47, 1.48, 1.49, 1.50, 1.51, 1.52, 1.53, 1.54, 1.55, 1.56, 1.57, 1.58, 1.59, 1.60,
                  1.61, 1.62, 1.63, 1.64, 1.65, 1.66, 1.67, 1.68, 1.69, 1.70, 1.71, 1.72, 1.73, 1.74, 1.75,
                  1.76, 1.77, 1.78, 1.79, 1.80, 1.81, 1.82, 1.83, 1.84, 1.85, 1.86, 1.87, 1.88, 1.89, 1.90,
                  1.91, 1.92, 1.93, 1.94, 1.95, 1.96, 1.97, 1.98, 1.99, 2.00, 2.02, 2.04, 2.06, 2.08, 2.10,
                  2.12, 2.14, 2.16, 2.18, 2.20, 2.22, 2.24, 2.26, 2.28, 2.30, 2.32, 2.34, 2.36, 2.38, 2.40,
                  2.42, 2.44, 2.46, 2.48, 2.50, 2.52, 2.54, 2.56, 2.58, 2.60, 2.62, 2.64, 2.66, 2.68, 2.70,
                  2.72, 2.74, 2.76, 2.78, 2.80, 2.82, 2.84, 2.86, 2.88, 2.90, 2.92, 2.94, 2.96, 2.98, 3.00,
                  3.05, 3.10, 3.15, 3.20, 3.25, 3.30, 3.35, 3.40, 3.45, 3.50, 3.55, 3.60, 3.65, 3.70, 3.75,
                  3.80, 3.85, 3.90, 3.95, 4.00, 4.10, 4.20, 4.30, 4.40, 4.50, 4.60, 4.70, 4.80, 4.90, 5.00,
                  5.10, 5.20, 5.30, 5.40, 5.50, 5.60, 5.70, 5.80, 5.90, 6.00, 6.20, 6.40, 6.60, 6.80, 7.00,
                  7.20, 7.40, 7.60, 7.80, 8.00, 8.20, 8.40, 8.60, 8.80, 9.00, 9.20, 9.40, 9.60, 9.80, 10.00,
                  10.50, 11.00, 11.50, 12.00, 12.50, 13.00, 13.50, 14.00, 14.50, 15.00, 15.50, 16.00, 16.50,
                  17.00, 17.50, 18.00, 18.50, 19.00, 19.50, 20.00, 21.00, 22.00, 23.00, 24.00, 26.00, 28.00,
                  29.00, 30.00, 31.00, 32.00, 34.00, 36.00, 38.00, 40.00, 41.00, 42.00, 44.00, 46.00, 48.00,
                  50.00, 51.00, 55.00, 60.00, 61.00, 65.00, 66.00, 67.00, 70.00, 71.00, 75.00, 76.00, 80.00,
                  81.00, 85.00, 90.00, 91.00, 95.00, 100.00, 101.00, 110.00, 111.00, 120.00, 126.00, 130.00,
                  140.00, 150.00, 151.00, 160.00, 170.00, 176.00, 180.00, 190.00, 200.00, 201.00, 210.00,
                  220.00, 226.00, 230.00, 240.00, 250.00, 251.00, 260.00, 270.00, 276.00, 280.00, 290.00,
                  300.00, 301.00, 310.00, 320.00, 330.00, 340.00, 350.00, 351.00, 360.00, 370.00, 380.00,
                  390.00, 400.00, 401.00, 410.00, 420.00, 430.00, 440.00, 450.00, 460.00, 470.00, 480.00,
                  490.00, 500.00, 501.00, 510.00, 520.00, 530.00, 540.00, 550.00, 560.00, 570.00, 580.00,
                  590.00, 600.00, 610.00, 620.00, 630.00, 640.00, 650.00, 660.00, 670.00, 680.00, 690.00,
                  700.00, 710.00, 720.00, 730.00, 740.00, 750.00, 751.00, 760.00, 770.00, 780.00, 790.00,
                  800.00, 810.00, 820.00, 830.00, 840.00, 850.00, 860.00, 870.00, 880.00, 890.00, 900.00,
                  910.00, 920.00, 930.00, 940.00, 950.00, 960.00, 970.00, 980.00, 990.00, 1000.00, 1001.00]
        return ladder